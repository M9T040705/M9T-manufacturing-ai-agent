"""修复登录失败限制"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''async def login(req: LoginRequest):
    """登录，返回token和用户信息"""
    user = state.verify_user(req.username, req.password)
    if not user:
        raise HTTPException(401, "用户名或密码错误")
    token = secrets.token_hex(16)
    user["token"] = token
    user["permissions"] = state.user_permissions(user["role"])
    user["role_name"] = ROLE_NAMES.get(user["role"], user["role"])
    _tokens[token] = user
    return user'''

new = '''# 登录失败计数（安全加固）
_login_failures: dict = {}
MAX_FAIL = 5
LOCK_TIME = 300  # 5分钟

async def login(req: LoginRequest):
    """登录，返回token和用户信息"""
    from datetime import datetime
    now = datetime.now().timestamp()
    fails = _login_failures.get(req.username, {"count": 0, "lock_until": 0})
    if fails["lock_until"] > now:
        remain = int((fails["lock_until"] - now) / 60)
        raise HTTPException(429, f"失败次数过多，请{remain}分钟后再试")

    user = state.verify_user(req.username, req.password)
    if not user:
        fails["count"] += 1
        if fails["count"] >= MAX_FAIL:
            fails["lock_until"] = now + LOCK_TIME
            fails["count"] = 0
        _login_failures[req.username] = fails
        raise HTTPException(401, "用户名或密码错误")

    if req.username in _login_failures:
        del _login_failures[req.username]

    token = secrets.token_hex(16)
    user["token"] = token
    user["permissions"] = state.user_permissions(user["role"])
    user["role_name"] = ROLE_NAMES.get(user["role"], user["role"])
    _tokens[token] = user
    return user'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
