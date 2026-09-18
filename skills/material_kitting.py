"""
场景4：生产计划 · 齐套与欠料预警 —— 对应图4场景一
基于BOM、库存、在途和排产，提前识别缺料风险。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    kb = engine.kb
    steps = []

    steps.append("调BOM、库存、在途、订单、排产")
    bom = conn.query_plm("bom")
    inv = conn.query_erp("inventory")
    stock = conn.query_wms("stock")
    po = conn.query_erp("purchase_orders")
    wo = conn.query_mes("work_orders")
    engine.audit.log("取数", "BOM+库存+在途+工单", {"bom": len(bom), "inv": len(inv), "wo": len(wo)})

    inv_map = {i["material"]: i for i in inv}
    stock_map = {s["material"]: s for s in stock}
    po_map = {}
    for p in po:
        po_map.setdefault(p["material"], []).append(p)

    steps.append("自动核对缺口量与到货时间")
    shortfalls = []
    for w in wo:
        product = w["product"]
        bom_list = next((b["components"] for b in bom if b["product"] == product), [])
        for comp in bom_list:
            mat = comp["material"]
            need = comp["qty_per"] * (w["qty"] - w["completed"])
            on_hand = inv_map.get(mat, {}).get("stock_qty", 0)
            in_transit = stock_map.get(mat, {}).get("in_transit", 0)
            available = on_hand + in_transit
            gap = need - available
            if gap > 0:
                # 查到货时间
                arrivals = po_map.get(mat, [])
                eta = arrivals[0]["expected_arrival"] if arrivals else "未知"
                shortfalls.append({
                    "work_order": w["wo_no"],
                    "product": product,
                    "material": mat,
                    "need": round(need, 1),
                    "available": available,
                    "gap": round(gap, 1),
                    "eta": eta,
                    "line": w["line"],
                })

    engine.audit.log("分析", "缺料计算完成", {"shortfall_count": len(shortfalls)})

    steps.append("识别会影响的工单与交期")
    lines = []
    for s in shortfalls:
        impact = "🔴 高" if s["gap"] > s["need"] * 0.3 else "🟡 中"
        lines.append(
            f"{impact} 工单{s['work_order']}（{s['product']}，{s['line']}）\n"
            f"   物料：{s['material']}\n"
            f"   需求{s['need']} / 可用{s['available']} → 缺口{s['gap']}\n"
            f"   预计到货：{s['eta']}"
        )

    if shortfalls:
        answer = "⚠ 齐套检查发现以下缺料风险：\n\n" + "\n\n".join(lines)
        answer += "\n\n💡 建议：优先催料到料，或调整排产顺序。"
        actions = ["停线/改排产/放行"]
    else:
        answer = "✅ 当前在制工单物料齐套，无缺料风险。"
        actions = []

    return AgentResponse(
        question=question,
        intent="material_kitting",
        steps_taken=steps,
        answer=answer,
        data_summary={"缺料项": len(shortfalls)},
        actions_proposed=actions,
    )
