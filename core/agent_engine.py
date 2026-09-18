"""
Agent引擎 —— 对应图3"一句话问下去，Agent在工厂里会怎么跑"
听懂业务口径 → 拆解任务 → 调系统取数 → 组织结论和动作
升级：出站安全扫描 + 对话持久化 + 规则版本冻结
"""
from dataclasses import dataclass, field
from typing import Callable, Optional

from .audit_log import AuditLog
from .data_connector import DataConnector
from .human_review import HumanReviewGate
from .knowledge_base import KnowledgeBase
from .safety_scan import scan_output
from .llm_client import LLMClient
from .model_router import ModelRouter


@dataclass
class AgentResponse:
    """Agent一次完整响应：问→跑→交"""
    question: str
    intent: str                    # 识别出的业务意图
    steps_taken: list[str] = field(default_factory=list)   # "跑"的过程
    answer: str = ""               # "交"给用户的结论
    data_summary: dict = field(default_factory=dict)        # 关键数据
    need_human_review: bool = False
    review_request: dict = None
    actions_proposed: list[str] = field(default_factory=list)
    trace_id: str = ""


class AgentEngine:
    """
    制造业Agent引擎。
    每个场景skill注册一个处理函数，引擎按意图分发。
    """

    def __init__(self, connector: DataConnector = None,
                 kb: KnowledgeBase = None,
                 review_gate: HumanReviewGate = None):
        self.connector = connector or DataConnector()
        self.kb = kb or KnowledgeBase()
        self.review = review_gate or HumanReviewGate()
        self.audit = AuditLog()
        self._skills: dict[str, Callable] = {}   # intent -> handler
        self._cache: dict = {}                    # 结果缓存：key -> (answer, timestamp)
        self._cache_ttl = 300                     # 缓存有效期5分钟
        self._dash_cache: dict = {}                # 看板/日报预计算缓存
        self._last_equip_snapshot: dict = {}       # 设备状态快照（增量更新用）
        self.llm = LLMClient()                    # 大模型客户端（DeepSeek）
        self.model_router = ModelRouter()          # 模型路由器

    def register_skill(self, intent: str, handler: Callable):
        """注册场景技能。handler签名: (question, engine) -> AgentResponse"""
        self._skills[intent] = handler

    def detect_intent(self, question: str) -> str:
        """
        意图识别。MVP用关键词匹配，真实部署可接LLM做语义理解。
        注意顺序：更具体的意图先匹配，避免"今天设备要盯什么"被日报抢走。
        """
        q = question
        # 最具体的先匹配
        if any(k in q for k in ["对账", "三单", "应付", "发票"]):
            return "procurement_reconciliation"
        if any(k in q for k in ["设备", "点检", "维保", "停机", "报警", "检修"]):
            return "equipment_maintenance"
        if any(k in q for k in ["追溯", "客诉", "哪一段", "批次", "不良", "归因"]):
            return "quality_traceability"
        if any(k in q for k in ["缺料", "齐套", "会不会缺", "欠料", "BOM"]):
            return "material_kitting"
        if any(k in q for k in ["交期", "什么时候能出", "什么时候能交货", "多久能出"]):
            return "delivery_quotation"
        if any(k in q for k in ["今天", "盯什么", "日报", "一页", "今天工厂"]):
            return "daily_briefing"
        # 【优化4】高频简单问题模板化：直接查表，不进分析引擎
        if any(k in q for k in ["库存多少", "库存有多少", "查库存", "库存状态"]):
            return "quick_query"
        if any(k in q for k in ["设备状态", "设备怎么样", "有几台报警", "今天报警"]):
            return "quick_query"
        return "general"

    def ask(self, question: str, user: str = "用户") -> AgentResponse:
        """主入口：用户问一句话，Agent跑完返回结果"""
        # 【优化1】结果缓存：5分钟内重复问题直接返回
        cache_key = f"{question.strip()}"
        cached = self._cache.get(cache_key)
        if cached:
            answer, ts = cached
            import time
            if time.time() - ts < self._cache_ttl:
                self.audit = AuditLog()
                self.audit.log("缓存命中", "直接返回缓存结果", {"question": question})
                resp = AgentResponse(question=question, intent="cached", answer=answer)
                resp.trace_id = self.audit.session_id
                self.audit.save()
                return resp

        self.audit = AuditLog()  # 每次对话独立审计session
        self.audit.log("用户提问", "接收问题", {"question": question, "user": user})

        intent = self.detect_intent(question)
        self.audit.log("意图识别", "识别业务意图", {"intent": intent})

        handler = self._skills.get(intent)
        if handler is None:
            resp = AgentResponse(
                question=question,
                intent=intent,
                answer=f"抱歉，我目前还不理解这个问题（识别为：{intent}）。"
                       f"你可以试试问：\n"
                       f"- 「这个月对账有没有异常？」\n"
                       f"- 「这单什么时候能出？」\n"
                       f"- 「今天工厂我该盯什么？」\n"
                       f"- 「下周线会不会缺料？」\n"
                       f"- 「今天这台设备要盯什么？」\n"
                       f"- 「这批客诉是哪一段出的？」",
            )
            resp.trace_id = self.audit.session_id
            return resp

        resp: AgentResponse = handler(question, self)
        resp.trace_id = self.audit.session_id

        # 【大模型集成】heavy级别自动调DeepSeek润色回答
        if self.llm.enabled:
            scene_map = {
                "procurement_reconciliation": "reconciliation",
                "delivery_quotation": "delivery",
                "daily_briefing": "daily",
                "material_kitting": "kitting",
                "equipment_maintenance": "equipment",
                "quality_traceability": "quality",
            }
            scene = scene_map.get(intent, "")
            level = self.model_router.get_model_level(scene, question)
            if level == "heavy":
                system = "你是制造业AI助手，基于以下规则分析结果，用自然的语言重新组织回答，保留关键数据，不要编造信息。"
                user = f"用户问题：{question}\n\n规则分析结果：{resp.answer}\n\n请用更专业、更易懂的语言重新组织回答："
                llm_answer = self.llm.chat(system, user)
                if llm_answer:
                    resp.answer = llm_answer
                    self.audit.log("大模型", "DeepSeek润色完成", {"level": level})

        # 出站安全扫描：输出前过滤敏感信息（对应Ha7ch经验：Model last）
        resp.answer = scan_output(resp.answer)

        # 检查建议的动作是否需要人审
        if resp.actions_proposed:
            for action in resp.actions_proposed:
                gate = self.review.check(action, {"summary": resp.answer[:200]})
                if gate["need_review"]:
                    resp.need_human_review = True
                    req = gate["request"]
                    resp.review_request = {
                        "request_id": req.request_id,
                        "action": req.action,
                        "risk_level": req.risk_level.value,
                        "approver": req.approver_role,
                    }
                    self.audit.log("人审", f"高风险动作需审批: {action}",
                                   {"request_id": req.request_id, "approver": req.approver_role})

        self.audit.log("交付", "返回结论", {"answer": resp.answer[:500]})
        # 【优化1】写入缓存（高风险审批类不缓存）
        if not resp.need_human_review:
            import time
            self._cache[cache_key] = (resp.answer, time.time())
        self.audit.save()
        return resp
