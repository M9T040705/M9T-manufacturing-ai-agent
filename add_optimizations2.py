"""加定时预计算+历史案例复用+增量更新"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加定时预计算（在启动事件里）
old_startup = """@app.on_event("startup")
async def startup():
    pass"""

new_startup = """@app.on_event("startup")
async def startup():
    # 【优化2】定时预计算：启动时先跑一遍日报，存到缓存
    import threading
    def precompute():
        import time
        while True:
            try:
                # 每天早上8点跑一次日报预计算
                now = time.localtime()
                if now.tm_hour == 8:
                    resp = engine.ask("今天工厂我该盯什么", user="system")
                    engine._dash_cache["daily_briefing"] = (resp.answer, time.time())
                    print(f"[预计算] 日报已缓存 @ {time.ctime()}")
            except Exception as e:
                print(f"[预计算] 失败: {e}")
            time.sleep(3600)  # 每小时检查一次
    threading.Thread(target=precompute, daemon=True).start()
    # 启动时先跑一次
    try:
        resp = engine.ask("今天工厂我该盯什么", user="system")
        engine._dash_cache["daily_briefing"] = (resp.answer, time.time())
        print("[预计算] 启动日报已缓存")
    except Exception as e:
        print(f"[预计算] 启动失败: {e}")"""

content = content.replace(old_startup, new_startup)

# 2. 历史案例复用：在ask接口里，跑完后查👍案例附在后面
old_ask_api = """    resp = engine.ask(question, user=user.get("username", "用户"))
    return {
        "answer": resp.answer,
        "intent": resp.intent,
        "need_review": resp.need_human_review,
        "review": resp.review_request,
    }"""

new_ask_api = """    resp = engine.ask(question, user=user.get("username", "用户"))
    # 【优化3】历史案例复用：如果有👍的历史案例，附在回答后面
    scene_map = {
        "procurement_reconciliation": "reconciliation",
        "delivery_quotation": "delivery",
        "daily_briefing": "daily",
        "material_kitting": "kitting",
        "equipment_maintenance": "equipment",
        "quality_traceability": "quality",
    }
    scene = scene_map.get(resp.intent, "")
    if scene:
        examples = state.get_good_examples(scene, limit=1)
        if examples and examples[0]["question"] != question:
            resp.answer += f"\\n\\n💡 参考历史成功案例：\\n用户问：{examples[0]['question']}\\n当时回答：{examples[0]['answer'][:200]}..."
    return {
        "answer": resp.answer,
        "intent": resp.intent,
        "need_review": resp.need_human_review,
        "review": resp.review_request,
    }"""

content = content.replace(old_ask_api, new_ask_api)

# 3. 增量更新：设备看板API只返回变化的设备
old_equip_api = """@app.get("/api/equipment/status")
async def equipment_status(user: dict = Depends(get_current_user)):
    \"\"\"设备状态看板\"\"\"
    machines = engine.connector.query_scada("equipment")
    alarms = engine.connector.query_scada("alarms")
    active_alarms = [a for a in alarms if a.get("status") == "active"]
    return {
        "machines": machines,
        "active_alarms": active_alarms,
    }"""

new_equip_api = """@app.get("/api/equipment/status")
async def equipment_status(user: dict = Depends(get_current_user)):
    \"\"\"设备状态看板（增量更新：只返回变化的设备）\"\"\"
    machines = engine.connector.query_scada("equipment")
    alarms = engine.connector.query_scada("alarms")
    active_alarms = [a for a in alarms if a.get("status") == "active"]

    # 【优化5】增量更新：对比上次快照，只标变化的设备
    prev = engine._last_equip_snapshot
    changed = []
    for m in machines:
        mid = m["equip_id"]
        old = prev.get(mid)
        if not old or old.get("status") != m.get("status") or old.get("alarm") != m.get("alarm"):
            changed.append(mid)
        m["changed"] = mid in changed
    # 更新快照
    engine._last_equip_snapshot = {m["equip_id"]: m for m in machines}

    return {
        "machines": machines,
        "active_alarms": active_alarms,
        "changed_count": len(changed),
    }"""

content = content.replace(old_equip_api, new_equip_api)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
