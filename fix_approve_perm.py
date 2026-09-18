"""修复审批接口权限漏洞"""
path = r"E:\FDE项目\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 修待审批列表：需要登录，且只显示当前用户能审批的
old_pending = '''@app.get("/api/pending")
async def list_pending():
    """待审批列表"""
    pending = engine.review.pending_list()
    return [
        {
            "id": r.request_id,
            "action": r.action,
            "risk": r.risk_level.value,
            "approver": r.approver_role,
            "status": r.status.value,'''

new_pending = '''@app.get("/api/pending")
async def list_pending(user: dict = Depends(get_current_user)):
    """待审批列表（只显示当前用户能审批的）"""
    role = user["role"]
    all_pending = engine.review.pending_list()
    # 只显示需要当前角色审批的（管理员看全部）
    pending = [r for r in all_pending if role == "admin" or r.approver_role == role]
    return [
        {
            "id": r.request_id,
            "action": r.action,
            "risk": r.risk_level.value,
            "approver": r.approver_role,
            "status": r.status.value,'''

content = content.replace(old_pending, new_pending)

# 2. 修审批接口：需要登录，且是审批人
old_approve = '''@app.post("/api/approve/{request_id}")
async def approve(request_id: str, approver: str = "当前用户"):
    r = engine.review.approve(request_id, approver)
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "approved", "id": r.request_id}'''

new_approve = '''@app.post("/api/approve/{request_id}")
async def approve(request_id: str, user: dict = Depends(get_current_user)):
    # 只有审批人角色能审批
    if user["role"] not in ["admin", "boss"]:
        raise HTTPException(403, "你没有审批权限")
    r = engine.review.approve(request_id, user["username"])
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "approved", "id": r.request_id}'''

content = content.replace(old_approve, new_approve)

# 3. 修驳回接口
old_reject = '''@app.post("/api/reject/{request_id}")
async def reject(request_id: str, approver: str = "当前用户"):
    r = engine.review.reject(request_id, approver)
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "rejected", "id": r.request_id}'''

new_reject = '''@app.post("/api/reject/{request_id}")
async def reject(request_id: str, user: dict = Depends(get_current_user)):
    if user["role"] not in ["admin", "boss"]:
        raise HTTPException(403, "你没有审批权限")
    r = engine.review.reject(request_id, user["username"])
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "rejected", "id": r.request_id}'''

content = content.replace(old_reject, new_reject)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
