"""测试模型配置"""
import requests

# 管理员登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 列出所有场景的模型配置
r = requests.get("http://localhost:8502/api/model-config", headers=headers)
configs = r.json()
print("=== 各部门模型配置 ===")
for c in configs:
    print(f"  {c['department']:8s} | {c['level_name']:8s} | {c['speed']} | {c['cost']} | {c['description']}")

# 2. 测试修改模型等级
r = requests.put("http://localhost:8502/api/model-config/reconciliation",
    headers=headers, json={"model_level": "heavy"})
print(f"\n=== 修改财务部模型等级为heavy ===")
print(f"  结果: {r.json()}")

# 3. 改回来
r = requests.put("http://localhost:8502/api/model-config/reconciliation",
    headers=headers, json={"model_level": "standard"})
print(f"\n=== 改回standard ===")
print(f"  结果: {r.json()}")

# 4. 看模型等级说明
r = requests.get("http://localhost:8502/api/model-levels", headers=headers)
print(f"\n=== 模型等级说明 ===")
for k, v in r.json().items():
    print(f"  {v['name']}: {v['description']}")
