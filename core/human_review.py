"""
人审与边界控制模块 —— 对应图5"哪些动作必须留给人审"和图3第6个能力
Agent可以提建议、做准备、写回待办，但高风险动作必须有人拍板。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(str, Enum):
    PENDING = "待审批"
    APPROVED = "已批准"
    REJECTED = "已驳回"


@dataclass
class ReviewRequest:
    """一条人工审批请求"""
    request_id: str
    action: str               # 动作描述
    risk_level: RiskLevel
    approver_role: str        # 应该谁审
    context: dict = field(default_factory=dict)   # 建议内容/数据快照
    status: ReviewStatus = ReviewStatus.PENDING
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    comment: str = ""


# 高风险动作清单（对应图5）
HIGH_RISK_ACTIONS = {
    "对外承诺交期": {"risk": RiskLevel.HIGH, "approver": "销售负责人"},
    "付款/折扣/退款": {"risk": RiskLevel.HIGH, "approver": "财务负责人"},
    "停线/改排产/放行": {"risk": RiskLevel.HIGH, "approver": "生产负责人"},
    "召回/判责/对外质量回复": {"risk": RiskLevel.HIGH, "approver": "质量负责人"},
    "越权访问/敏感审批": {"risk": RiskLevel.CRITICAL, "approver": "系统管理员"},
}


class HumanReviewGate:
    """人审闸门：高风险动作必须经过审批才能执行"""

    def __init__(self):
        self.pending: list[ReviewRequest] = []

    def check(self, action: str, context: dict = None) -> dict:
        """
        检查一个动作是否需要人审。
        返回 {"need_review": bool, "request": ReviewRequest|None}
        """
        matched = None
        for keyword, rule in HIGH_RISK_ACTIONS.items():
            if keyword in action:
                matched = rule
                break

        if matched is None:
            # 低风险动作，Agent可直接执行
            return {"need_review": False, "request": None}

        req = ReviewRequest(
            request_id=f"R-{datetime.now().strftime('%H%M%S%f')}",
            action=action,
            risk_level=matched["risk"],
            approver_role=matched["approver"],
            context=context or {},
        )
        self.pending.append(req)
        return {"need_review": True, "request": req}

    def approve(self, request_id: str, approver: str, comment: str = ""):
        for r in self.pending:
            if r.request_id == request_id:
                r.status = ReviewStatus.APPROVED
                r.decided_by = approver
                r.decided_at = datetime.now()
                r.comment = comment
                return r
        return None

    def reject(self, request_id: str, approver: str, comment: str = ""):
        for r in self.pending:
            if r.request_id == request_id:
                r.status = ReviewStatus.REJECTED
                r.decided_by = approver
                r.decided_at = datetime.now()
                r.comment = comment
                return r
        return None

    def pending_list(self) -> list[ReviewRequest]:
        return [r for r in self.pending if r.status == ReviewStatus.PENDING]
