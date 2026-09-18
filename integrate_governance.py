"""集成数据治理和自进化到app_server"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加导入
old_import = "from core.model_router import ModelRouter"
new_import = """from core.model_router import ModelRouter
from core.data_governance import DataGovernance
from core.self_evolution import SelfEvolution"""
content = content.replace(old_import, new_import)

# 2. 初始化实例
old_init = "model_router = ModelRouter()"
new_init = """model_router = ModelRouter()
data_governance = DataGovernance()
self_evolution = SelfEvolution(state)"""
content = content.replace(old_init, new_init)

# 3. 加API（在llm-status后面）
old_llm = '''@app.get("/api/llm-status")
async def llm_status(user = Depends(get_current_user)):
    """大模型状态"""
    return engine.llm.get_status()'''

new_llm = old_llm + '''


# ── 数据治理 + 自进化 API ──────────────────
@app.get("/api/governance/report")
async def governance_report(user = Depends(require_admin)):
    """数据质量报告（FDE第二层）"""
    return data_governance.get_quality_report()

@app.get("/api/evolution/report")
async def evolution_report(user = Depends(require_admin)):
    """自进化报告（FDE第五层）"""
    return self_evolution.get_full_report()'''

content = content.replace(old_llm, new_llm)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
