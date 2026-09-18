"""验证运维功能"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 系统状态
r = requests.get("http://localhost:8502/api/ops/status", headers=headers)
print("=== 系统状态 ===")
print(r.json())

# 2. 创建快照
r = requests.post("http://localhost:8502/api/ops/snapshot", headers=headers)
print(f"\n=== 创建快照 ===")
print(r.json())

# 3. 列出快照
r = requests.get("http://localhost:8502/api/ops/snapshots", headers=headers)
print(f"\n=== 快照列表 ===")
print(f"  共{len(r.json())}个快照")

# 4. 备份数据库
r = requests.post("http://localhost:8502/api/ops/backup", headers=headers)
print(f"\n=== 备份数据库 ===")
print(r.json())

# 5. 错误日志
r = requests.get("http://localhost:8502/api/ops/errors", headers=headers)
print(f"\n=== 错误日志 ===")
print(f"  共{len(r.json())}条错误")
