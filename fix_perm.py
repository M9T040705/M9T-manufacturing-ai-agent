"""修复权限越权问题：消息通知按角色过滤"""
path = r"E:\FDE项目\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 替换消息通知接口
old_notif = '''@app.get("/api/notifications")
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
    return raw'''

new_notif = '''@app.get("/api/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    """消息通知列表（按角色过滤，带已读状态）"""
    import hashlib
    conn = engine.connector
    role = user["role"]
    perms = state.user_permissions(role)
    raw = []

    # 设备报警：只有生产、厂长、管理员能看到
    if role in ["admin", "boss", "production"]:
        machines = conn.query_scada("equipment")
        for m in machines:
            if m["status"] == "报警":
                title = f"{m['equip_id']} 报警"
                desc = ", ".join(m.get("alarm", []))
                raw.append({"type": "alarm", "title": title, "desc": desc, "time": "现在"})

    # 待审批：只有审批人角色能看到
    if role in ["admin", "boss"]:
        pending = engine.review.pending_list()
        for p in pending:
            # 只显示需要当前角色审批的
            if role == "admin" or p["approver_role"] == role:
                title = f"待审批：{p['action']}"
                desc = f"需{p['approver_role']}审批"
                raw.append({"type": "approval", "title": title, "desc": desc, "time": "现在"})

    # 库存预警：生产、采购、厂长、管理员能看到
    if role in ["admin", "boss", "production"]:
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
    return raw'''

content = content.replace(old_notif, new_notif)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
