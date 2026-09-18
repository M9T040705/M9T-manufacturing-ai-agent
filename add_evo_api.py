"""加自进化升级API"""
path = r"E:\FDE项目\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 在evolution接口后面加新的API
old_evo = '''@app.get("/api/evolution/report")
async def evolution_report(user = Depends(require_admin)):
    """自进化报告（FDE第五层）"""
    return self_evolution.get_full_report()'''

new_evo = old_evo + '''


class RuleSuggestionRequest(BaseModel):
    scene: str
    title: str
    content: str

@app.post("/api/evolution/test-rule")
async def test_new_rule(req: RuleSuggestionRequest, user = Depends(require_admin)):
    """Level 3: 新规则自动回测验证"""
    result = self_evolution.auto_regression_test(req.model_dump())
    return result

@app.get("/api/evolution/cross-impact/{scene}")
async def cross_scene_impact(scene: str, user = Depends(require_admin)):
    """Level 4: 跨场景影响分析"""
    return self_evolution.cross_scene_impact(scene)'''

content = content.replace(old_evo, new_evo)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
