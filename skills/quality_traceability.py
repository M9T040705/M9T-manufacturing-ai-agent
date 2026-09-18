"""
场景6：质量 · 批次追溯与归因 —— 对应图4场景三
打通批次、工艺、检验和设备数据，快速定位问题批次。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    kb = engine.kb
    steps = []

    steps.append("拉批次、工艺、检验、投料、设备、班次数据")
    inspections = conn.query_qms("inspections")
    defects = conn.query_qms("defects")
    in_out = conn.query_wms("in_out")
    routing = conn.query_plm("routing")
    engine.audit.log("取数", "质量追溯数据", {"inspections": len(inspections), "defects": len(defects)})

    # 找不合格批次
    failed = [i for i in inspections if i["result"] == "不合格"]
    steps.append("关联缺陷、异常记录和流转轨迹")

    body = "🔍 质量批次追溯结果：\n\n"
    if not failed:
        body += "✅ 当前无不合格批次记录。"
        return AgentResponse(question=question, intent="quality_traceability",
                             steps_taken=steps, answer=body, data_summary={})

    for fi in failed:
        batch = fi["batch"]
        body += f"📦 问题批次：{batch}（{fi['product']}）\n"
        body += f"   检验项：{fi['test_item']}，实测{fi['value']}（标准{fi['standard']}）\n"

        # 关联缺陷记录
        related = [d for d in defects if d["batch"] == batch]
        if related:
            for d in related:
                body += f"   📋 不良：{d['defect_type']} {d['qty']}件\n"
                body += f"   🏭 产线：{d['line']} | 设备：{d['equipment']} | 班次：{d['shift']} | 操作：{d['operator']}\n"

                # 调用知识库根因经验
                exp = kb.query_experience(fi["product"] + fi["test_item"])
                if exp:
                    body += f"   💡 历史经验：{exp.get('root_cause', '')}\n"
                    body += f"   🔧 建议措施：{exp.get('fix', '')}\n"

        # 正向影响范围：同批次投料去向
        same_batch_out = [o for o in in_out if o.get("batch") == batch and o["type"] == "出库"]
        if same_batch_out:
            body += f"   🚚 已出库：{len(same_batch_out)}笔\n"

        body += "\n"

    steps.append("分析影响范围与可能原因")
    body += "⚠ 以上为系统自动分析结果，召回/判责/对外回复需质量负责人确认。"

    return AgentResponse(
        question=question,
        intent="quality_traceability",
        steps_taken=steps,
        answer=body,
        data_summary={"不合格批次": len(failed)},
        actions_proposed=["召回/判责/对外质量回复"],
    )
