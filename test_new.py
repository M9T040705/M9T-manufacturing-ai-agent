"""测试新功能"""
import requests

# 登录厂长
r = requests.post("http://localhost:8502/api/login", json={"username":"boss","password":"boss123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 测试dashboard
r = requests.get("http://localhost:8502/api/dashboard", headers=headers)
d = r.json()
print("=== 首页看板 ===")
for k, v in d.items():
    print(f"  {k}: {v}")

# 2. 测试通知
r = requests.get("http://localhost:8502/api/notifications", headers=headers)
notifs = r.json()
print(f"\n=== 通知列表（{len(notifs)}条）===")
for n in notifs:
    print(f"  [{n['type']}] {n['title']}: {n['desc']}")

# 3. 测试导出
r = requests.post("http://localhost:8502/api/export/equipment", headers=headers)
print(f"\n=== 导出测试 ===")
print(f"  HTTP {r.status_code}, {len(r.text)} bytes")
print(f"  前100字: {r.text[:100]}")
