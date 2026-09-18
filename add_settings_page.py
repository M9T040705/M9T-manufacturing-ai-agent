"""加前端个人设置页面"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 侧边栏加个人设置入口
old_sidebar = """      <div class="p-4 border-t border-slate-100">
        <div class="flex items-center justify-between">
          <div>
            <div class="text-sm font-medium text-slate-700">${currentUser.display_name}</div>
            <div class="text-xs text-slate-400">${currentUser.role_name}</div>
          </div>
          <button onclick="doLogout()" class="text-xs text-slate-400 hover:text-red-500">退出</button>
        </div>
      </div>"""

new_sidebar = """      <div class="p-4 border-t border-slate-100">
        <div class="flex items-center justify-between">
          <div class="flex-1 cursor-pointer" onclick="navTo('settings')">
            <div class="text-sm font-medium text-slate-700">${currentUser.display_name}</div>
            <div class="text-xs text-slate-400">${currentUser.role_name}</div>
          </div>
          <button onclick="doLogout()" class="text-xs text-slate-400 hover:text-red-500">退出</button>
        </div>
      </div>"""

content = content.replace(old_sidebar, new_sidebar)

# 2. renderMain加路由
old_render = """  else if (currentPage === "evolution") main.innerHTML = renderEvolutionPage();"""
new_render = """  else if (currentPage === "evolution") main.innerHTML = renderEvolutionPage();
  else if (currentPage === "settings") main.innerHTML = renderSettingsPage();"""
content = content.replace(old_render, new_render)

# 3. bind加路由
old_bind = """  else if (currentPage === "evolution") bindEvolutionEvents();"""
new_bind = """  else if (currentPage === "evolution") bindEvolutionEvents();
  else if (currentPage === "settings") bindSettingsEvents();"""
content = content.replace(old_bind, new_bind)

# 4. 加个人设置页面
old_evolution = """async function bindEvolutionEvents() {"""
new_evolution = '''function renderSettingsPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">⚙️ 个人设置</h1>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div class="max-w-2xl space-y-6">
        <div class="bg-white rounded-xl border p-5">
          <div class="font-medium text-slate-800 mb-4">👤 账号信息</div>
          <div class="space-y-2 text-sm">
            <div><span class="text-slate-500">用户名：</span>${currentUser.username}</div>
            <div><span class="text-slate-500">姓名：</span>${currentUser.display_name}</div>
            <div><span class="text-slate-500">角色：</span>${currentUser.role_name}</div>
            <div><span class="text-slate-500">部门：</span>${currentUser.department || "-"}</div>
          </div>
        </div>
        <div class="bg-white rounded-xl border p-5">
          <div class="font-medium text-slate-800 mb-4">🔑 修改密码</div>
          <div class="space-y-3 max-w-sm">
            <input id="oldPwd" type="password" placeholder="旧密码" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
            <input id="newPwd" type="password" placeholder="新密码（至少6位）" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
            <input id="confirmPwd" type="password" placeholder="确认新密码" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
            <button onclick="changePwd()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">修改密码</button>
          </div>
        </div>
        <div class="bg-white rounded-xl border p-5">
          <div class="font-medium text-slate-800 mb-4">ℹ️ 系统信息</div>
          <div id="sysInfo" class="text-sm text-slate-600 space-y-1"></div>
        </div>
      </div>
    </div>`;
}

async function bindSettingsEvents() {
  try {
    const r = await fetch("/api/health");
    const d = await r.json();
    document.getElementById("sysInfo").innerHTML = `
      <div>系统版本：v${d.version}</div>
      <div>数据库：${d.database === "mysql" ? "MySQL（生产）" : "SQLite（演示）"}</div>
      <div>大模型：${d.llm_enabled ? "✅ 已接入" : "❌ 未配置"}</div>
      <div>运行状态：✅ 正常</div>`;
  } catch(e) {}
}

async function changePwd() {
  const old = document.getElementById("oldPwd").value;
  const p1 = document.getElementById("newPwd").value;
  const p2 = document.getElementById("confirmPwd").value;
  if (!old || !p1) { toast("请填完整", "error"); return; }
  if (p1 !== p2) { toast("两次密码不一致", "error"); return; }
  if (p1.length < 6) { toast("密码至少6位", "error"); return; }
  try {
    await api("/api/change-password", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({old_password: old, new_password: p1})});
    toast("密码修改成功");
    document.getElementById("oldPwd").value = "";
    document.getElementById("newPwd").value = "";
    document.getElementById("confirmPwd").value = "";
  } catch(e) { toast(e.message, "error"); }
}

async function bindEvolutionEvents() {'''

content = content.replace(old_evolution, new_evolution)

# 5. 改doLogout，调用后端logout接口
old_logout = """function doLogout() {
  token = ""; currentUser = null;
  localStorage.removeItem("token"); localStorage.removeItem("user");
  render();
}"""

new_logout = """function doLogout() {
  // 调后端logout，token失效
  fetch("/api/logout", {method:"POST", headers:{"Authorization": "Bearer " + token}}).catch(()=>{});
  token = ""; currentUser = null;
  localStorage.removeItem("token"); localStorage.removeItem("user");
  render();
}"""

content = content.replace(old_logout, new_logout)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("frontend done")
