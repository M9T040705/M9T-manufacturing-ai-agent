"""修复设备API增量更新"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.get("/api/equipment/status")
async def equipment_status(user: dict = Depends(get_current_user)):
    """设备状态看板：全厂设备红绿黄"""
    conn = engine.connector
    machines = conn.query_scada("equipment")
    alarms = conn.query_scada("alarms")
    return {"machines": machines, "active_alarms": alarms}'''

new = '''@app.get("/api/equipment/status")
async def equipment_status(user: dict = Depends(get_current_user)):
    """设备状态看板：全厂设备红绿黄（增量更新：只标变化的设备）"""
    conn = engine.connector
    machines = conn.query_scada("equipment")
    alarms = conn.query_scada("alarms")

    # 【优化5】增量更新：对比上次快照，只标变化的设备
    prev = engine._last_equip_snapshot
    changed = []
    for m in machines:
        mid = m["equip_id"]
        old = prev.get(mid)
        if not old or old.get("status") != m.get("status") or old.get("alarm") != m.get("alarm"):
            changed.append(mid)
        m["changed"] = mid in changed
    engine._last_equip_snapshot = {m["equip_id"]: m for m in machines}

    return {"machines": machines, "active_alarms": alarms, "changed_count": len(changed)}'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
