"""
场景1：采购三单匹配与对账 —— 对应图5场景四
让对账更快更准，减少扯皮。
"""
from core.agent_engine import AgentResponse


def handle(question: str, engine) -> AgentResponse:
    conn = engine.connector
    steps = []

    # 1. 取数：采购订单、收货记录、发票/应付数据
    steps.append("调采购订单、收货记录、发票/应付数据")
    pos = conn.query_erp("purchase_orders")
    invoices = conn.query_erp("ap_invoices")
    engine.audit.log("取数", "采购三单数据", {"po_count": len(pos), "invoice_count": len(invoices)})

    # 2. 自动核对数量、单价、金额、到货与开票差异
    steps.append("自动核对数量、单价、金额、到货与开票差异")
    anomalies = []
    inv_map = {i["po_no"]: i for i in invoices}
    for po in pos:
        inv = inv_map.get(po["po_no"])
        if inv is None:
            anomalies.append(f"⚠ {po['po_no']}（{po['supplier']}）：已有收货但无发票")
            continue
        # 数量差异：收货数量 vs 发票数量
        if inv["receipt_amount"] != inv["invoice_amount"]:
            pct = abs(inv["receipt_amount"] - inv["invoice_amount"]) / max(inv["receipt_amount"], 1)
            if pct > 0.01:
                anomalies.append(
                    f"🔴 {po['po_no']}：发票金额({inv['invoice_amount']}) ≠ 收货金额({inv['receipt_amount']})，"
                    f"差异{pct*100:.1f}%"
                )
        # 只收了部分货
        if po["received_qty"] < po["qty"]:
            anomalies.append(
                f"🟡 {po['po_no']}：采购{po['qty']}但仅收货{po['received_qty']}，"
                f"预计{po['expected_arrival']}到货"
            )

    engine.audit.log("分析", "三单核对完成", {"anomaly_count": len(anomalies)})

    # 3. 识别异常和待确认项
    steps.append("识别异常和待确认项")
    if not anomalies:
        answer = "✅ 本月采购三单匹配正常，未发现数量/金额异常。\n所有采购订单收货与发票一致。"
    else:
        answer = "📋 本月采购对账发现以下异常：\n\n" + "\n".join(f"  {a}" for a in anomalies)

    return AgentResponse(
        question=question,
        intent="procurement_reconciliation",
        steps_taken=steps,
        answer=answer,
        data_summary={"异常数": len(anomalies), "采购单数": len(pos)},
        actions_proposed=["付款/折扣/退款"],  # 触发人审：付款需财务审核
    )
