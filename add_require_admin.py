"""给app_server.py加require_admin依赖"""
path = r"E:\fde\app_server.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """    return user


# ── 请求模型"""

new = """    return user


async def require_admin(request: Request) -> dict:
    \"\"\"仅管理员可访问\"\"\"
    user = await get_current_user(request)
    if user.get("role") != "admin":
        from fastapi import HTTPException as HE
        raise HE(status_code=403, detail="仅管理员可访问")
    return user


# ── 请求模型"""

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
