"""把LLM集成到agent_engine和app_server"""
path = r"E:\fde\core\agent_engine.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 导入LLMClient
old_import = "from .safety_scan import scan_output"
new_import = """from .safety_scan import scan_output
from .llm_client import LLMClient
from .model_router import ModelRouter"""
content = content.replace(old_import, new_import)

# 2. 在__init__里初始化
old_init = """        self._cache: dict = {}                    # 结果缓存：key -> (answer, timestamp)
        self._cache_ttl = 300                     # 缓存有效期5分钟
        self._dash_cache: dict = {}                # 看板/日报预计算缓存
        self._last_equip_snapshot: dict = {}       # 设备状态快照（增量更新用）"""
new_init = """        self._cache: dict = {}                    # 结果缓存：key -> (answer, timestamp)
        self._cache_ttl = 300                     # 缓存有效期5分钟
        self._dash_cache: dict = {}                # 看板/日报预计算缓存
        self._last_equip_snapshot: dict = {}       # 设备状态快照（增量更新用）
        self.llm = LLMClient()                    # 大模型客户端（DeepSeek）
        self.model_router = ModelRouter()          # 模型路由器"""
content = content.replace(old_init, new_init)

# 3. 在ask方法里，规则跑完后，如果是heavy级别，调大模型润色
old_answer = """        resp: AgentResponse = handler(question, self)
        resp.trace_id = self.audit.session_id

        # 出站安全扫描：输出前过滤敏感信息（对应Ha7ch经验：Model last）
        resp.answer = scan_output(resp.answer)"""

new_answer = """        resp: AgentResponse = handler(question, self)
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
                user = f"用户问题：{question}\\n\\n规则分析结果：{resp.answer}\\n\\n请用更专业、更易懂的语言重新组织回答："
                llm_answer = self.llm.chat(system, user)
                if llm_answer:
                    resp.answer = llm_answer
                    self.audit.log("大模型", "DeepSeek润色完成", {"level": level})

        # 出站安全扫描：输出前过滤敏感信息（对应Ha7ch经验：Model last）
        resp.answer = scan_output(resp.answer)"""

content = content.replace(old_answer, new_answer)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("agent_engine done")
