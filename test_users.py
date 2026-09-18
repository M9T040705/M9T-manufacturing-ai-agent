"""测试用户管理"""
import requests

# 管理员登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 列出所有用户
r = requests.get("http://localhost:8502/api/users", headers=headers)
users = r.json()
print(f"=== 用户列表（{len(users)}个）===")
for u in users:
    print(f"  {u['display_name']:10s} @{u['username']:10s} {u['role_name']:10s} {u.get('department','')}")

# 2. 创建新用户
r = requests.post("http://localhost:8502/api/users", headers=headers,
    json={"username":"zhang3","password":"123456","display_name":"张三","role":"production","department":"生产部"})
print(f"\n=== 创建用户 ===")
print(f"  状态: {'成功' if r.ok else '失败'}")
print(f"  结果: {r.json()}")

# 3. 验证新用户能登录
r = requests.post("http://localhost:8502/api/login", json={"username":"zhang3","password":"123456"})
print(f"\n=== 新用户登录测试 ===")
print(f"  状态: {'成功' if r.ok else '失败'}")
if r.ok:
    print(f"  权限: {r.json()['permissions']['scenes']}")

# 4. 普通用户不能访问用户管理
r2 = requests.post("http://localhost:8502/api/login", json={"username":"finance","password":"fin123"})
fin_token = r2.json()["token"]
r = requests.get("http://localhost:8502/api/users", headers={"Authorization": f"Bearer {fin_token}"})
print(f"\n=== 权限测试（财务访问用户管理）===")
print(f"  状态码: {r.status_code}（应该是403）")
