"""验证补全的功能"""
import requests

# 1. 健康检查
r = requests.get("http://localhost:8502/api/health")
print("=== 健康检查 ===")
print(r.json())

# 2. 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 3. 修改密码（用错误旧密码）
r = requests.post("http://localhost:8502/api/change-password", headers=headers,
    json={"old_password": "wrong", "new_password": "newpass123"})
print(f"\n=== 修改密码（错误旧密码）===")
print(f"  状态码: {r.status_code}, {r.json().get('detail','')}")

# 4. 退出登录
r = requests.post("http://localhost:8502/api/logout", headers=headers)
print(f"\n=== 退出登录 ===")
print(f"  状态: {r.json()}")

# 5. 退出后再用token访问（应该401）
r = requests.get("http://localhost:8502/api/me", headers=headers)
print(f"\n=== 退出后再访问（应该401）===")
print(f"  状态码: {r.status_code}")
