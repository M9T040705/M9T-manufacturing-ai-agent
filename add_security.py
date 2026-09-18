"""加安全加固：登录失败次数限制"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 加登录失败计数
old_login = '''@app.post("/api/login")
async def login(req: LoginRequest):
    """登录，返回token和用户信息"""
    user = state.verify_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    permissions = state.user_permissions(user["role"])
    token = secrets.token_hex(16)
    _tokens[token] = user
    return {
        "token": token,
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "role_name": ROLE_NAMES.get(user["role"], user["role"]),
        "department": user.get("department", ""),
        "permissions": permissions,
    }'''

new_login = '''# 登录失败计数（安全加固）
_login_failures: dict = {}
MAX_FAIL = 5
LOCK_TIME = 300  # 5分钟

@app.post("/api/login")
async def login(req: LoginRequest):
    """登录，返回token和用户信息"""
    # 安全加固：失败次数限制
    now = datetime.now().timestamp()
    fails = _login_failures.get(req.username, {"count": 0, "lock_until": 0})
    if fails["lock_until"] > now:
        remain = int((fails["lock_until"] - now) / 60)
        raise HTTPException(status_code=429, detail=f"失败次数过多，请{remain}分钟后再试")

    user = state.verify_user(req.username, req.password)
    if not user:
        fails["count"] += 1
        if fails["count"] >= MAX_FAIL:
            fails["lock_until"] = now + LOCK_TIME
            fails["count"] = 0
        _login_failures[req.username] = fails
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功，清空失败计数
    if req.username in _login_failures:
        del _login_failures[req.username]

    permissions = state.user_permissions(user["role"])
    token = secrets.token_hex(16)
    _tokens[token] = user
    return {
        "token": token,
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "role_name": ROLE_NAMES.get(user["role"], user["role"]),
        "department": user.get("department", ""),
        "permissions": permissions,
    }'''

content = content.replace(old_login, new_login)

# 确保导入datetime
if "from datetime import datetime" not in content:
    content = content.replace("import secrets", "import secrets\nfrom datetime import datetime")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
