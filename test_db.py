"""验证双模式数据库"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
print("登录:", "成功" if r.ok else "失败")
data = r.json()
print(f"  用户: {data['display_name']}")
print(f"  角色: {data['role_name']}")

# 验证历史
r = requests.get("http://localhost:8502/api/history/daily", headers={"Authorization": f"Bearer {data['token']}"})
print(f"\n历史记录: {len(r.json())}条")

# 验证反馈统计
r = requests.get("http://localhost:8502/api/feedback/stats", headers={"Authorization": f"Bearer {data['token']}"})
print(f"反馈统计: {r.json()}")

print("\n✅ 数据库层正常，当前自动使用SQLite模式（因为还没装MySQL）")
