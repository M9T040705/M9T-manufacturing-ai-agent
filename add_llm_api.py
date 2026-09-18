"""在app_server里加LLM状态API"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 加API（在模型配置API后面）
old = '''@app.get("/api/model-levels")
async def get_model_levels(user = Depends(require_admin)):
    """列出所有模型等级"""
    return model_router._config.get("model_levels", {})'''

new = old + '''

@app.get("/api/llm-status")
async def llm_status(user = Depends(get_current_user)):
    """大模型状态"""
    return engine.llm.get_status()'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
