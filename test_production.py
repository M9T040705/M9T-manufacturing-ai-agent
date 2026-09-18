"""验证投产版"""
import requests

# 1. 页面能不能打开
r = requests.get("http://localhost:8502/")
print(f"页面状态码: {r.status_code}")
print(f"有没有外网CDN: {'cdn.tailwindcss.com' in r.text}")
print(f"有没有demo提示: {'测试账号' in r.text}")

# 2. 本地CSS能不能加载
r = requests.get("http://localhost:8502/static/css/tailwind.js")
print(f"\n本地CSS状态码: {r.status_code}, 大小: {len(r.text)}字节")

# 3. 登录失败限制
print("\n=== 测试登录失败限制 ===")
for i in range(6):
    r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"wrong"})
    print(f"  第{i+1}次: 状态码={r.status_code}, {r.json().get('detail','')}")
