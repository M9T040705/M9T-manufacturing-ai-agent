"""测试登录和权限隔离"""
import requests

BASE = "http://localhost:8502"

# 1. 财务登录
r = requests.post(f"{BASE}/api/login", json={"username":"finance","password":"fin123"})
fin = r.json()
print(f"财务登录: {fin['display_name']} / {fin['role_name']}")
print(f"  可访问场景: {fin['permissions']['scenes']}")
print(f"  可访问页面: {fin['permissions']['pages']}")

# 2. 质量登录
r = requests.post(f"{BASE}/api/login", json={"username":"qc","password":"qc123"})
qc = r.json()
print(f"\n质量登录: {qc['display_name']} / {qc['role_name']}")
print(f"  可访问场景: {qc['permissions']['scenes']}")

# 3. 厂长登录
r = requests.post(f"{BASE}/api/login", json={"username":"boss","password":"boss123"})
boss = r.json()
print(f"\n厂长登录: {boss['display_name']} / {boss['role_name']}")
print(f"  可访问场景: {boss['permissions']['scenes']}")

# 4. 财务尝试问质量问题（应该被拦截）
print("\n--- 权限测试 ---")
fin_token = fin["token"]
r = requests.post(f"{BASE}/api/ask", json={"question":"这批客诉追溯一下"},
    headers={"Authorization": f"Bearer {fin_token}"})
print(f"财务问质量问题: {r.json()['answer'][:60]}")

# 5. 财务问对账（应该正常）
r = requests.post(f"{BASE}/api/ask", json={"question":"这个月对账有没有异常？"},
    headers={"Authorization": f"Bearer {fin_token}"})
print(f"财务问对账: {r.json()['answer'][:60]}")

# 6. 错误密码
r = requests.post(f"{BASE}/api/login", json={"username":"finance","password":"wrong"})
print(f"\n错误密码: HTTP {r.status_code}")

print("\n✅ 权限隔离测试完成")
