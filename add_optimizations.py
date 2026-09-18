"""给agent_engine.py加5个省token优化"""
path = r"E:\fde\core\agent_engine.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加缓存层（在__init__里）
old_init = """        self._skills: dict[str, Callable] = {}   # intent -> handler"""
new_init = """        self._skills: dict[str, Callable] = {}   # intent -> handler
        self._cache: dict = {}                    # 结果缓存：key -> (answer, timestamp)
        self._cache_ttl = 300                     # 缓存有效期5分钟
        self._dash_cache: dict = {}                # 看板/日报预计算缓存
        self._last_equip_snapshot: dict = {}       # 设备状态快照（增量更新用）"""
content = content.replace(old_init, new_init)

# 2. 在ask方法开头加缓存查询
old_ask_start = """    def ask(self, question: str, user: str = "用户") -> AgentResponse:
        \"\"\"主入口：用户问一句话，Agent跑完返回结果\"\"\"
        self.audit = AuditLog()  # 每次对话独立审计session
        self.audit.log("用户提问", "接收问题", {"question": question, "user": user})"""

new_ask_start = """    def ask(self, question: str, user: str = "用户") -> AgentResponse:
        \"\"\"主入口：用户问一句话，Agent跑完返回结果\"\"\"
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
        self.audit.log("用户提问", "接收问题", {"question": question, "user": user})"""
content = content.replace(old_ask_start, new_ask_start)

# 3. 在ask方法末尾加缓存写入
old_ask_end = """        self.audit.log("交付", "返回结论", {"answer": resp.answer[:500]})
        self.audit.save()
        return resp"""
new_ask_end = """        self.audit.log("交付", "返回结论", {"answer": resp.answer[:500]})
        # 【优化1】写入缓存（高风险审批类不缓存）
        if not resp.need_human_review:
            import time
            self._cache[cache_key] = (resp.answer, time.time())
        self.audit.save()
        return resp"""
content = content.replace(old_ask_end, new_ask_end)

# 4. 加高频问题模板化（简单查询直接查表，不进分析引擎）
# 加在detect_intent方法后面
old_detect_end = """        if any(k in q for k in ["今天", "盯什么", "日报", "一页", "今天工厂"]):
            return "daily_briefing"
        return "general\""""

new_detect_end = """        if any(k in q for k in ["今天", "盯什么", "日报", "一页", "今天工厂"]):
            return "daily_briefing"
        # 【优化4】高频简单问题模板化：直接查表，不进分析引擎
        if any(k in q for k in ["库存多少", "库存有多少", "查库存", "库存状态"]):
            return "quick_query"
        if any(k in q for k in ["设备状态", "设备怎么样", "有几台报警", "今天报警"]):
            return "quick_query"
        return "general\""""
content = content.replace(old_detect_end, new_detect_end)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
