"""修复所有越权接口"""
path = r"E:\FDE项目\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 历史记录：需要登录，且只能看自己有权限的场景
old_history = '''@app.get("/api/history/{scene}")
async def get_history(scene: str):
    """获取某场景的对话历史"""
    return state.get_history(scene)'''

new_history = '''@app.get("/api/history/{scene}")
async def get_history(scene: str, user: dict = Depends(get_current_user)):
    """获取某场景的对话历史（只有有权限的角色能看）"""
    perms = state.user_permissions(user["role"])
    # 管理员和厂长能看所有，其他角色只能看自己的
    if user["role"] not in ["admin", "boss"] and scene not in perms["scenes"]:
        raise HTTPException(403, "你没有权限查看这个场景的历史")
    return state.get_history(scene)'''

content = content.replace(old_history, new_history)

# 2. 数据表列表：需要登录
old_tables = '''@app.get("/api/tables")
async def list_tables():
    """所有数据表状态"""
    uploaded = data_store.list_uploaded()'''

new_tables = '''@app.get("/api/tables")
async def list_tables(user: dict = Depends(get_current_user)):
    """所有数据表状态"""
    uploaded = data_store.list_uploaded()'''

content = content.replace(old_tables, new_tables)

# 3. 数据状态：需要登录
old_ds = '''@app.get("/api/data-status")
async def data_status():
    """数据源接入状态总览：每个系统域接了几张表"""
    uploaded = data_store.list_uploaded()'''

new_ds = '''@app.get("/api/data-status")
async def data_status(user: dict = Depends(get_current_user)):
    """数据源接入状态总览：每个系统域接了几张表"""
    uploaded = data_store.list_uploaded()'''

content = content.replace(old_ds, new_ds)

# 4. 规则列表：需要登录
old_rules = '''@app.get("/api/rules")
async def list_rules():
    """列出所有规则及其版本"""
    return engine.kb.list_rules()'''

new_rules = '''@app.get("/api/rules")
async def list_rules(user: dict = Depends(get_current_user)):
    """列出所有规则及其版本"""
    return engine.kb.list_rules()'''

content = content.replace(old_rules, new_rules)

# 5. 技能列表：需要登录
old_skills = '''@app.get("/api/skills")
async def list_skills():
    """列出所有技能插件（从yaml加载）"""
    return skill_registry.list_all()'''

new_skills = '''@app.get("/api/skills")
async def list_skills(user: dict = Depends(get_current_user)):
    """列出所有技能插件（从yaml加载）"""
    return skill_registry.list_all()'''

content = content.replace(old_skills, new_skills)

# 6. 导出接口：需要登录，且只能导出自己有权限的场景
old_export = '''@app.post("/api/export/{scene}")
async def export_scene(scene: str):'''

new_export = '''@app.post("/api/export/{scene}")
async def export_scene(scene: str, user: dict = Depends(get_current_user)):
    """导出场景数据（只有有权限的角色能导出）"""
    perms = state.user_permissions(user["role"])
    if user["role"] not in ["admin", "boss"] and scene not in perms["scenes"]:
        raise HTTPException(403, "你没有权限导出这个场景的数据")'''

content = content.replace(old_export, new_export)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
