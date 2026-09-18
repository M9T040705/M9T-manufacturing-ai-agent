"""测试通知已读功能"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"boss","password":"boss123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 获取通知列表
r = requests.get("http://localhost:8502/api/notifications", headers=headers)
notifs = r.json()
print(f"=== 通知列表（{len(notifs)}条）===")
for n in notifs:
    print(f"  [{'未读' if not n['read'] else '已读'}] {n['title']} (id={n['id']})")

# 2. 标记第一条已读
if notifs:
    nid = notifs[0]["id"]
    r = requests.post(f"http://localhost:8502/api/notifications/{nid}/read", headers=headers)
    print(f"\n=== 标记单条已读（{nid}）===")
    print(f"  状态: {r.json()}")

    # 3. 再查，看已读状态
    r = requests.get("http://localhost:8502/api/notifications", headers=headers)
    notifs2 = r.json()
    unread = [n for n in notifs2 if not n["read"]]
    print(f"\n=== 标记后 ===")
    print(f"  未读: {len(unread)}条")
    for n in notifs2:
        print(f"  [{'未读' if not n['read'] else '已读'}] {n['title']}")

# 4. 全部已读
r = requests.post("http://localhost:8502/api/notifications/read-all", headers=headers)
print(f"\n=== 全部标为已读 ===")
print(f"  结果: {r.json()}")

# 5. 再查
r = requests.get("http://localhost:8502/api/notifications", headers=headers)
notifs3 = r.json()
unread = [n for n in notifs3 if not n["read"]]
print(f"  未读剩余: {len(unread)}条")
