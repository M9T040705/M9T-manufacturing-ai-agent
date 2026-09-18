"""
审计日志模块 —— 对应图5"留痕可追溯"和图3第7个能力
所有Agent取数、分析、建议、动作都留痕，可回放可审计。
"""
import json
import os
from datetime import datetime
from pathlib import Path

AUDIT_DIR = Path(__file__).parent.parent / "audit"
AUDIT_DIR.mkdir(exist_ok=True)


class AuditLog:
    """全链路审计日志：取数 → 分析 → 建议 → 动作，每步留痕"""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.entries = []

    def log(self, stage: str, action: str, detail: dict, actor: str = "agent"):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "stage": stage,       # 取数/分析/建议/动作/审批
            "action": action,
            "actor": actor,       # agent / 用户名
            "detail": detail,
        }
        self.entries.append(entry)
        return entry

    def get_trace(self) -> list:
        return self.entries

    def save(self):
        """持久化到audit目录，供审计回放"""
        path = AUDIT_DIR / f"audit_{self.session_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
        return str(path)
