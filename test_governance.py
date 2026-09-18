"""测试数据治理+自进化"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 数据治理报告
r = requests.get("http://localhost:8502/api/governance/report", headers=headers)
g = r.json()
print("=== 数据治理报告 ===")
print(f"  总问题数: {g['total_issues']}")
print(f"  高/中/低: {g['high']}/{g['medium']}/{g['low']}")
print(f"  血缘记录: {len(g['lineage'])}条")

# 2. 自进化报告
r = requests.get("http://localhost:8502/api/evolution/report", headers=headers)
e = r.json()
print(f"\n=== 自进化报告 ===")
m = e["metrics"]
print(f"  总反馈: {m['total_feedback']}")
print(f"  好评: {m['good_count']} / 差评: {m['bad_count']}")
print(f"  满意度: {m['satisfaction_rate']*100:.0f}%")
print(f"  成熟度: {m['maturity']} - {m['maturity_desc']}")
print(f"  优化建议: {len(e['suggestions'])}条")
for s in e["suggestions"]:
    print(f"    - {s['message']}")
