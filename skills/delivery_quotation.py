"""
场景2：销售交期答复 —— 对应图5场景五
让交期答复更快更稳，减少来回确认。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    kb = engine.kb
    steps = []

    # 从问题中识别订单关键词，MVP默认查最新订单
    steps.append("拉订单、库存、在制、排产、产能和异常信息")
    orders = conn.query_erp("orders")
    inventory = conn.query_erp("inventory")
    work_orders = conn.query_mes("work_orders")
    bom = conn.query_plm("bom")
    engine.audit.log("取数", "订单+库存+工单+BOM",
                      {"orders": len(orders), "inventory": len(inventory)})

    inv_map = {i["material"]: i for i in inventory}
    wo_map = {w["product"]: w for w in work_orders}
    bom_map = {b["product"]: b["components"] for b in bom}

    lines = []
    actions = []
    for order in orders[:3]:
        product = order["product"]
        wo = wo_map.get(product, {})
        bom_list = bom_map.get(product, [])

        # 物料齐套检查
        material_risk = []
        for comp in bom_list:
            mat = inv_map.get(comp["material"], {})
            need = comp["qty_per"] * order["qty"]
            have = mat.get("on_hand", 0)
            if have < need:
                material_risk.append(f"{comp['material']}缺{need-have:.0f}{comp['unit']}")

        # 综合判断最早可交期
        completed = wo.get("completed", 0)
        qty = wo.get("qty", order["qty"])
        pct = completed / max(qty, 1) * 100 if qty else 0

        if material_risk:
            status = f"⚠ 物料未齐套（{'、'.join(material_risk)}），需等采购到货后排产"
            eta = "待物料到货+加工周期确认"
        elif pct >= 80:
            status = f"生产中，完工率{pct:.0f}%"
            eta = wo.get("planned_finish", "按计划")
        elif pct == 0:
            status = "待投产"
            eta = "需排产后确认"
        else:
            status = f"生产中，完工率{pct:.0f}%"
            eta = wo.get("planned_finish", "按计划")

        lines.append(
            f"📦 订单 {order['order_no']}（{order['customer']}）\n"
            f"   产品：{product} ×{order['qty']}\n"
            f"   客户要求交期：{order['due_date']}\n"
            f"   当前状态：{status}\n"
            f"   建议答复交期：{eta}"
        )

    engine.audit.log("分析", "交期综合判断完成", {"order_count": len(orders)})

    answer = "根据订单、库存、在制、排产综合判断：\n\n" + "\n\n".join(lines)
    answer += "\n\n⚠ 以上为系统建议交期，对外承诺前需销售确认。"

    actions.append("对外承诺交期")  # 触发人审

    return AgentResponse(
        question=question,
        intent="delivery_quotation",
        steps_taken=steps,
        answer=answer,
        data_summary={"订单数": len(orders)},
        actions_proposed=actions,
    )
