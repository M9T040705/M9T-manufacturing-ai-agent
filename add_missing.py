"""补全遗漏功能：修改密码/退出登录/健康检查/数据删除"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加修改密码接口
old_me = '''@app.get("/api/me")
async def me(user: dict = Depends(get_current_user)):
    """当前用户信息和权限"""
    user["permissions"] = state.user_permissions(user["role"])
    user["role_name"] = ROLE_NAMES.get(user["role"], user["role"])
    return user'''

new_me = old_me + '''


class ChangePwdRequest(BaseModel):
    old_password: str
    new_password: str

@app.post("/api/change-password")
async def change_password(req: ChangePwdRequest, user: dict = Depends(get_current_user)):
    """用户自己修改密码"""
    import hashlib
    old_hash = hashlib.sha256(req.old_password.encode()).hexdigest()
    # 验证旧密码
    if not state.verify_user(user["username"], req.old_password):
        raise HTTPException(400, "旧密码不正确")
    # 更新密码
    state.reset_password(user["id"], req.new_password)
    return {"status": "ok", "message": "密码修改成功"}

@app.post("/api/logout")
async def logout(request: Request, user: dict = Depends(get_current_user)):
    """退出登录，token失效"""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if token in _tokens:
        del _tokens[token]
    return {"status": "ok"}

@app.get("/api/health")
async def health():
    """系统健康检查"""
    import os
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": state.mode,
        "llm_enabled": engine.llm.enabled,
        "uptime": "running",
    }

@app.delete("/api/upload/{table_key}")
async def delete_upload(table_key: str, user: dict = Depends(require_admin)):
    """删除上传的数据表（管理员）"""
    from core import data_store
    try:
        data_store.delete_table(table_key)
        return {"status": "ok", "message": "已删除，恢复示例数据"}
    except Exception as e:
        raise HTTPException(400, f"删除失败: {str(e)}")'''

content = content.replace(old_me, new_me)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("backend done")
