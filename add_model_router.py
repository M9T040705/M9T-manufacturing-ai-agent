"""集成ModelRouter到app_server.py"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加导入
old_import = "from core.skill_loader import SkillRegistry"
new_import = """from core.skill_loader import SkillRegistry
from core.model_router import ModelRouter"""
content = content.replace(old_import, new_import)

# 2. 初始化model_router
old_init = "state = StateStore()"
new_init = """state = StateStore()
model_router = ModelRouter()"""
content = content.replace(old_init, new_init)

# 3. 加模型管理API（在用户管理API后面）
old_users_end = '''@app.get("/api/roles")
async def list_roles(user = Depends(require_admin)):
    """列出所有角色（仅管理员）"""
    return state.list_roles()'''

new_users_end = old_users_end + '''


# ── 模型路由配置（仅admin）────────────────
@app.get("/api/model-config")
async def get_model_config(user = Depends(require_admin)):
    """列出所有场景的模型配置"""
    return model_router.list_scenes_config()

@app.put("/api/model-config/{scene}")
async def update_model_config(scene: str, req: dict, user = Depends(require_admin)):
    """更新某场景的模型等级"""
    new_level = req.get("model_level", "")
    ok = model_router.update_scene_level(scene, new_level)
    if not ok:
        raise HTTPException(status_code=400, detail="无效的模型等级或场景")
    return {"status": "ok", "scene": scene, "model_level": new_level}

@app.get("/api/model-levels")
async def get_model_levels(user = Depends(require_admin)):
    """列出所有模型等级"""
    return model_router._config.get("model_levels", {})'''

content = content.replace(old_users_end, new_users_end)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
