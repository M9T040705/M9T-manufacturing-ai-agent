"""测试单条通知已读API"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"boss","password":"boss123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 获取通知列表
r = requests.get("http://localhost:8502/api/notifications", headers=headers)
notifs = r.json()
print(f"通知列表: {len(notifs)}条")
for n in notifs:
    print(f"  id={n['id']} read={n['read']} title={n['title']}")

# 测试标记已读
if notifs:
    nid = notifs[0]["id"]
    print(f"\n尝试标记 {nid} 已读...")
    r = requests.post(f"http://localhost:8502/api/notifications/{nid}/read", headers=headers)
    print(f"  状态码: {r.status_code}")
    print(f"  响应: {r.text}")
