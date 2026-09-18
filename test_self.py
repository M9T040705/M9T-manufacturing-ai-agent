"""测试自进化和设备看板"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"prod","password":"prod123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 测试ask
r = requests.post("http://localhost:8502/api/ask", json={"question":"今天设备要盯什么？"}, headers=headers)
d = r.json()
print("=== Ask测试 ===")
print(f"意图: {d['intent']}")
print(f"回答前80字: {d['answer'][:80]}")

# 2. 测试反馈
r = requests.post("http://localhost:8502/api/feedback", json={
    "scene": "equipment", "question": "今天设备要盯什么？",
    "answer": d["answer"], "rating": "good", "comment": "很有用"
}, headers=headers)
print(f"\n=== 反馈测试 ===")
print(f"反馈: {r.json()}")

# 3. 测试反馈统计
r = requests.get("http://localhost:8502/api/feedback/stats", headers=headers)
print(f"统计: {r.json()}")

# 4. 测试设备状态看板
r = requests.get("http://localhost:8502/api/equipment/status", headers=headers)
data = r.json()
print(f"\n=== 设备状态看板 ===")
for m in data["machines"]:
    print(f'  {m["equip_id"]} {m["name"]}: {m["status"]} · {m["run_hours"]}h')
    if m["alarm"]:
        print(f'    报警: {", ".join(m["alarm"])}')

print(f"\n活跃报警: {len(data['active_alarms'])}条")
