"""改登录页标题"""
path = r"E:\FDE项目\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''<div class="text-3xl font-bold text-blue-600">FDE</div>
          <p class="text-xs text-slate-400 mt-1">工厂数字员工平台</p>'''

new = '''<div class="text-2xl font-bold text-blue-600">制造业AI Agent平台</div>
          <p class="text-xs text-slate-400 mt-1">工厂数字员工系统</p>'''

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
