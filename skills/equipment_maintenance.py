"""
场景5：设备维保 · 点检核修 —— 对应图4场景二
结合设备运行数据、点检记录和维修经验，识别异常风险。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    kb = engine.kb
    steps = []

    steps.append("读取报警、点检记录、运行时长、停机历史")
    equip = conn.query_scada("equipment")
    alarms = conn.query_scada("alarms")
    engine.audit.log("取数", "设备状态+报警记录", {"equip_count": len(equip)})

    steps.append("识别超期保养、重复故障、高风险点")
    risk_items = []
    for e in equip:
        # 有报警的设备
        if e["alarm"]:
            # 调用知识库经验
            exp = kb.query_experience(e["equip_id"])
            advice_lines = []
            if exp and "symptoms" in exp:
                for sym in e["alarm"]:
                    for k, v in exp["symptoms"].items():
                        if k in sym:
                            advice_lines.append(f"   💡 {k}：{v}")
            risk_items.append({
                "equip": e["equip_id"],
                "name": e["name"],
                "alarms": e["alarm"],
                "run_hours": e["run_hours"],
                "last_maint": e["last_maintenance"],
                "advice": advice_lines,
                "level": "高",
            })
        # 运行时长超期预警（假设5000小时需大修）
        elif e["run_hours"] > 5000:
            risk_items.append({
                "equip": e["equip_id"],
                "name": e["name"],
                "alarms": ["运行时长超5000小时，建议安排预防性检修"],
                "run_hours": e["run_hours"],
                "last_maint": e["last_maintenance"],
                "advice": [],
                "level": "中",
            })

    engine.audit.log("分析", "设备风险识别", {"risk_count": len(risk_items)})

    steps.append("调用维修经验与知识库")
    body = "🔧 今日设备点检与维保建议：\n\n"
    if not risk_items:
        body += "✅ 所有设备运行正常，无异常报警。"
    for r in risk_items:
        icon = "🔴" if r["level"] == "高" else "🟡"
        body += f"{icon} {r['equip']}（{r['name']}）— {r['level']}风险\n"
        body += f"   运行时长：{r['run_hours']}h | 上次保养：{r['last_maint']}\n"
        body += f"   报警：{'、'.join(r['alarms'])}\n"
        for a in r["advice"]:
            body += a + "\n"
        body += "\n"

    body += "💡 建议：高风险设备今日安排点检，维修方案由设备主管确认。"

    return AgentResponse(
        question=question,
        intent="equipment_maintenance",
        steps_taken=steps,
        answer=body,
        data_summary={"风险设备": len(risk_items)},
        actions_proposed=["停线/改排产/放行"],
    )
