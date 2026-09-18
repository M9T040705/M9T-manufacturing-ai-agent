"""快速验证脚本：不启动Web，直接测试6个场景Agent能否跑通"""
import sys
sys.path.insert(0, r"E:\fde")

from core.agent_engine import AgentEngine
from core.data_connector import DataConnector
from core.knowledge_base import KnowledgeBase
from core.human_review import HumanReviewGate
from skills import register_all_skills

# 初始化
engine = AgentEngine(
    connector=DataConnector(mode="mock"),
    kb=KnowledgeBase(),
    review_gate=HumanReviewGate(),
)
register_all_skills(engine)

# 测试6个场景
test_questions = [
    "这个月对账有没有异常？",
    "这单什么时候能出？",
    "今天工厂我该盯什么？",
    "下周线会不会缺料？",
    "今天这台设备要盯什么？",
    "这批客诉是哪一段出的？",
]

print("=" * 60)
print("制造业AI Agent MVP 验证")
print("=" * 60)

for q in test_questions:
    print(f"\n{'─' * 60}")
    print(f"❓ 用户问：{q}")
    resp = engine.ask(q)
    print(f"🎯 意图识别：{resp.intent}")
    print(f"📋 处理步骤：{' → '.join(resp.steps_taken)}")
    print(f"📤 Agent回答：\n{resp.answer}")
    if resp.need_human_review:
        print(f"🔴 需人审：{resp.review_request['action']}（{resp.review_request['approver']}）")
    print(f"📝 审计ID：{resp.trace_id}")

print(f"\n{'=' * 60}")
print(f"✅ 全部6个场景测试完成")
print(f"📋 待审批数：{len(engine.review.pending_list())}")
