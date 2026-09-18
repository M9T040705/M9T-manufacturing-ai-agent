"""修复语法错误"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''@app.post("/api/login")
# 登录失败计数（安全加固）
_login_failures: dict = {}
MAX_FAIL = 5
LOCK_TIME = 300  # 5分钟

async def login(req: LoginRequest):'''

new = '''# 登录失败计数（安全加固）
_login_failures: dict = {}
MAX_FAIL = 5
LOCK_TIME = 300  # 5分钟

@app.post("/api/login")
async def login(req: LoginRequest):'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
