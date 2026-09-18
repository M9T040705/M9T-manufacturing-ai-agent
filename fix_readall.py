"""修复read-all的hash不一致问题"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.post("/api/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """标记所有通知为已读"""
    # 重新拉一遍当前通知，全部标记
    conn = engine.connector
    raw = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            raw.append(f"alarm{m['equip_id']}报警")
    pending = engine.review.pending_list()
    for p in pending:
        raw.append(f"approval{p.action}")
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            raw.append(f"warning{i['material']}")
    import hashlib
    for s in raw:
        nid = hashlib.md5(s.encode()).hexdigest()[:12]
        state.mark_notif_read(nid, user["username"])
    return {"status": "ok", "marked": len(raw)}'''

new = '''@app.post("/api/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """标记所有通知为已读"""
    import hashlib
    conn = engine.connector
    raw = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            title = f"{m['equip_id']} 报警"
            desc = ", ".join(m.get("alarm", []))
            raw.append(("alarm", title, desc))
    pending = engine.review.pending_list()
    for p in pending:
        title = f"待审批：{p.action}"
        desc = f"需{p.approver_role}审批"
        raw.append(("approval", title, desc))
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            title = f"库存预警：{i['material']}"
            desc = f"库存{i['stock_qty']}{i['unit']}，低于安全线{i['safety_stock']}"
            raw.append(("warning", title, desc))
    marked = 0
    for typ, title, desc in raw:
        nid = hashlib.md5(f"{typ}{title}{desc}".encode()).hexdigest()[:12]
        state.mark_notif_read(nid, user["username"])
        marked += 1
    return {"status": "ok", "marked": marked}'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
