"""测试技能插件加载"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 测试技能列表
r = requests.get("http://localhost:8502/api/skills", headers=headers)
skills = r.json()
print("=== 技能插件列表 ===")
for s in skills:
    print(f'{s["icon"]} {s["name"]} ({s["id"]})')
    print(f'   触发词: {", ".join(s["triggers"])}')
    print(f'   数据源: {", ".join(s["data_sources"])}')
    print()

# 2. 测试ask还能正常工作
r = requests.post("http://localhost:8502/api/ask", json={"question":"这个月对账有没有异常？"}, headers=headers)
d = r.json()
print("=== Ask测试 ===")
print(f"意图: {d['intent']}")
print(f"回答前60字: {d['answer'][:60]}")
