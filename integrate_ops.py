"""集成OpsManager到app_server"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 加导入
old_import = "from core.self_evolution import SelfEvolution"
new_import = """from core.self_evolution import SelfEvolution
from core.ops_manager import OpsManager"""
content = content.replace(old_import, new_import)

# 2. 初始化
old_init = "self_evolution = SelfEvolution(state)"
new_init = """self_evolution = SelfEvolution(state)
ops = OpsManager()"""
content = content.replace(old_init, new_init)

# 3. 加API（在evolution后面）
old_evo = '''@app.get("/api/evolution/report")
async def evolution_report(user = Depends(require_admin)):
    """自进化报告（FDE第五层）"""
    return self_evolution.get_full_report()'''

new_evo = old_evo + '''


# ── 运维管理 API（仅admin）────────────────
@app.get("/api/ops/status")
async def ops_status(user = Depends(require_admin)):
    """系统运维状态"""
    return ops.get_system_status()

@app.get("/api/ops/snapshots")
async def list_snapshots(user = Depends(require_admin)):
    """列出所有快照"""
    return ops.list_snapshots()

@app.post("/api/ops/snapshot")
async def create_snapshot(user = Depends(require_admin)):
    """创建配置快照"""
    return ops.create_snapshot()

@app.post("/api/ops/rollback/{snapshot_name}")
async def rollback(snapshot_name: str, user = Depends(require_admin)):
    """一键回退到指定快照"""
    try:
        return ops.rollback_snapshot(snapshot_name)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/ops/backup")
async def backup_db(user = Depends(require_admin)):
    """备份数据库"""
    return ops.backup_database()

@app.get("/api/ops/errors")
async def error_logs(user = Depends(require_admin)):
    """获取错误日志"""
    return ops.get_error_logs()'''

content = content.replace(old_evo, new_evo)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
