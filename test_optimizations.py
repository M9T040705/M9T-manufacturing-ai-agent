"""测试5个优化"""
import requests
import time

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"boss","password":"boss123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 测试结果缓存：问两次同样的问题，第二次应该更快
print("=== 测试结果缓存 ===")
t1 = time.time()
r = requests.post("http://localhost:8502/api/ask", headers=headers,
    json={"question": "今天工厂我该盯什么？"})
t2 = time.time()
print(f"  第一次: {t2-t1:.2f}秒, intent={r.json()['intent']}")

t1 = time.time()
r = requests.post("http://localhost:8502/api/ask", headers=headers,
    json={"question": "今天工厂我该盯什么？"})
t2 = time.time()
print(f"  第二次: {t2-t1:.2f}秒, intent={r.json()['intent']}")
print(f"  第二次intent是cached吗: {r.json()['intent'] == 'cached'}")

# 2. 测试设备看板增量更新
print("\n=== 测试设备看板增量更新 ===")
r = requests.get("http://localhost:8502/api/equipment/status", headers=headers)
d = r.json()
print(f"  设备数: {len(d['machines'])}")
print(f"  变化设备数: {d['changed_count']}")

# 再查一次，应该变化数为0
r = requests.get("http://localhost:8502/api/equipment/status", headers=headers)
d = r.json()
print(f"  第二次查询变化数: {d['changed_count']}（应该是0，因为没变化）")

# 3. 测试历史案例复用
print("\n=== 测试历史案例复用 ===")
r = requests.post("http://localhost:8502/api/ask", headers=headers,
    json={"question": "下周线会不会缺料？"})
answer = r.json()["answer"]
has_example = "参考历史成功案例" in answer
print(f"  回答里有历史案例参考吗: {has_example}")
