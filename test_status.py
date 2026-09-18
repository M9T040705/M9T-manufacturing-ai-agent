"""测试数据状态接口"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 测试数据状态接口
r = requests.get("http://localhost:8502/api/data-status", headers=headers)
data = r.json()
print("=== 数据接入状态 ===")
for d in data:
    print(f'{d["domain"]:6} | {d["name"]} | {d["real"]}/{d["total"]} 已接入')
    for e in d["entities"]:
        status = "✅" if e["is_real"] else "⏳"
        print(f'  {status} {e["name"]}')
