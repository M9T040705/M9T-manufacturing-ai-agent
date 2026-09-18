"""改app_server.py的通知API，加已读功能"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 替换通知API
old = '''@app.get("/api/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    """消息通知列表"""
    conn = engine.connector
    notifs = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            notifs.append({"type": "alarm", "title": f"{m['equip_id']} 报警", "desc": ", ".join(m.get("alarm", [])), "time": "现在"})
    pending = engine.review.pending_list()
    for p in pending:
        notifs.append({"type": "approval", "title": f"待审批：{p.action}", "desc": f"需{p.approver_role}审批", "time": "现在"})
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            notifs.append({"type": "warning", "title": f"库存预警：{i['material']}", "desc": f"库存{i['stock_qty']}{i['unit']}，低于安全线{i['safety_stock']}", "time": "现在"})
    return notifs'''

new = '''@app.get("/api/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    """消息通知列表（带已读状态）"""
    import hashlib
    conn = engine.connector
    raw = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            title = f"{m['equip_id']} 报警"
            desc = ", ".join(m.get("alarm", []))
            raw.append({"type": "alarm", "title": title, "desc": desc, "time": "现在"})
    pending = engine.review.pending_list()
    for p in pending:
        title = f"待审批：{p.action}"
        desc = f"需{p.approver_role}审批"
        raw.append({"type": "approval", "title": title, "desc": desc, "time": "现在"})
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            title = f"库存预警：{i['material']}"
            desc = f"库存{i['stock_qty']}{i['unit']}，低于安全线{i['safety_stock']}"
            raw.append({"type": "warning", "title": title, "desc": desc, "time": "现在"})
    # 给每条通知生成唯一ID（基于内容hash）
    for n in raw:
        n["id"] = hashlib.md5(f"{n['type']}{n['title']}{n['desc']}".encode()).hexdigest()[:12]
    # 查已读状态
    read_set = state.get_read_notifs(user["username"])
    for n in raw:
        n["read"] = n["id"] in read_set
    # 未读排前面
    raw.sort(key=lambda x: x["read"])
    return raw


@app.post("/api/notifications/{notif_id}/read")
async def mark_notif_read(notif_id: str, user: dict = Depends(get_current_user)):
    """标记单条通知为已读"""
    state.mark_notif_read(notif_id, user["username"])
    return {"status": "ok"}


@app.post("/api/notifications/read-all")
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

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
