"""
场景3：管理每日一页 —— 对应图5场景六
让管理更聚焦，看清今天该盯什么。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    steps = []

    steps.append("汇总生产、质量、设备、交付、库存异常")
    wo = conn.query_mes("work_orders")
    defects = conn.query_qms("defects")
    equip = conn.query_scada("equipment")
    inv = conn.query_erp("inventory")
    engine.audit.log("取数", "全厂异常汇总", {"wo": len(wo), "defects": len(defects), "equip": len(equip)})

    alerts = []

    # 1. 设备报警
    for e in equip:
        if e["alarm"]:
            alerts.append(("高", f"🔧 {e['equip_id']}（{e['name']}）报警：{'、'.join(e['alarm'])}"))

    # 2. 质量异常
    for d in defects:
        alerts.append(("高", f"📋 {d['batch']} {d['defect_type']} {d['qty']}件（{d['line']} {d['shift']}）"))

    # 3. 库存低于安全线
    for i in inv:
        if i["stock_qty"] < i["safety_stock"]:
            alerts.append(("中", f"📦 {i['material']}库存{i['stock_qty']}{i['unit']}，"
                                  f"低于安全库存{i['safety_stock']}{i['unit']}"))

    # 4. 工单进度风险
    for w in wo:
        if w["status"] == "待投产":
            alerts.append(("中", f"🏭 工单{w['wo_no']}（{w['product']}）待投产，"
                                  f"计划{w['planned_finish']}完工"))

    steps.append("按影响程度排序")
    # 简单按严重程度排序：高在前
    order_map = {"高": 0, "中": 1, "低": 2}
    alerts.sort(key=lambda x: order_map.get(x[0], 9))

    steps.append("形成一页式日报")
    high = [a for a in alerts if a[0] == "高"]
    med = [a for a in alerts if a[0] == "中"]

    body = f"📊 今日工厂异常一页\n"
    body += f"━━━━━━━━━━━━━━━━━━\n"
    body += f"🔴 高优先级（{len(high)}项）：\n"
    for _, a in high:
        body += f"  {a}\n"
    body += f"\n🟡 中优先级（{len(med)}项）：\n"
    for _, a in med:
        body += f"  {a}\n"
    body += f"\n📌 关键指标：在制工单{len(wo)}个 | 报警设备{len([e for e in equip if e['alarm']])}台 | 质量异常{len(defects)}批"
    body += f"\n\n💡 建议优先处理：设备报警和质量异常需今日跟进。"

    return AgentResponse(
        question=question,
        intent="daily_briefing",
        steps_taken=steps,
        answer=body,
        data_summary={"高优先级": len(high), "中优先级": len(med)},
    )
