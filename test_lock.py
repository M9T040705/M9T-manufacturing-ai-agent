"""测试登录失败锁定"""
import requests
for i in range(7):
    r = requests.post("http://localhost:8502/api/login", json={"username":"testlock","password":"wrong"})
    detail = r.json().get("detail", "")
    print(f"第{i+1}次: {r.status_code} - {detail}")
