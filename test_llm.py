"""测试LLM集成"""
import requests

# 登录
r = requests.post("http://localhost:8502/api/login", json={"username":"admin","password":"admin123"})
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

# 1. 看大模型状态
r = requests.get("http://localhost:8502/api/llm-status", headers=headers)
print("=== 大模型状态 ===")
print(r.json())

# 2. 正常问一个问题（没填API key，应该走规则）
r = requests.post("http://localhost:8502/api/ask", headers=headers,
    json={"question": "这批客诉是哪一段出的？"})
d = r.json()
print(f"\n=== 测试问质量追溯 ===")
print(f"  intent: {d['intent']}")
print(f"  回答前100字: {d['answer'][:100]}")
print(f"  （没填API Key，走规则回答，正常）")
