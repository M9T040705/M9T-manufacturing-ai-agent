"""给index.html加用户管理页面"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 侧边栏加用户管理入口
old_sidebar = """    if (perms.pages.includes("audit")) navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="audit"><span>📝</span> 审计日志</a>`;
  }"""
new_sidebar = """    if (perms.pages.includes("audit")) navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="audit"><span>📝</span> 审计日志</a>`;
    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="users"><span>👥</span> 用户管理</a>`;
  }"""
content = content.replace(old_sidebar, new_sidebar)

# 2. renderMain加路由
old_render = """  else if (currentPage === "rules") main.innerHTML = renderRulesPage();"""
new_render = """  else if (currentPage === "rules") main.innerHTML = renderRulesPage();
  else if (currentPage === "users") main.innerHTML = renderUsersPage();"""
content = content.replace(old_render, new_render)

# 3. bind加路由
old_bind = """  else if (currentPage === "rules") bindRulesEvents();"""
new_bind = """  else if (currentPage === "rules") bindRulesEvents();
  else if (currentPage === "users") bindUsersEvents();"""
content = content.replace(old_bind, new_bind)

# 4. 在renderRulesPage函数后面加用户管理页面
old_rules_end = """async function bindRulesEvents() {
  const list = await api("/api/rules");
  document.getElementById("rulesList").innerHTML = list.map(r => `<div class="bg-white rounded-xl border p-4"><div class="font-medium">📖 ${r.topic}</div><div class="text-xs text-slate-500 mt-1">v${r.version} · ${r.approved_by}</div></div>`).join("");
}"""
new_rules_end = old_rules_end + """

function renderUsersPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">👥 用户管理</h1>
        <p class="text-sm text-slate-500 mt-1">添加部门账号、分配角色、重置密码</p>
      </div>
      <button id="addUserBtn" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm">+ 添加用户</button>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="userList" class="space-y-3 max-w-4xl"></div>
    </div>
    <div id="userModal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
      <div class="bg-white rounded-2xl p-6 w-96">
        <h3 class="text-lg font-bold mb-4" id="modalTitle">添加用户</h3>
        <div class="space-y-3">
          <input id="userName" type="text" placeholder="姓名（显示名）" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
          <input id="userAccount" type="text" placeholder="登录账号（英文/数字）" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
          <input id="userPwd" type="password" placeholder="初始密码" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
          <select id="userRole" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
            <option value="finance">财务</option>
            <option value="sales">销售</option>
            <option value="production">生产</option>
            <option value="quality">质量</option>
            <option value="manager">厂长/管理者</option>
            <option value="admin">系统管理员</option>
          </select>
          <input id="userDept" type="text" placeholder="部门（如：财务部）" class="w-full border border-slate-300 rounded-lg px-4 py-2 text-sm">
        </div>
        <div class="flex gap-2 mt-4">
          <button id="saveUserBtn" class="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg text-sm">保存</button>
          <button id="cancelUserBtn" class="flex-1 bg-slate-200 hover:bg-slate-300 py-2 rounded-lg text-sm">取消</button>
        </div>
      </div>
    </div>`;
}

async function bindUsersEvents() {
  await loadUserList();
  document.getElementById("addUserBtn").onclick = () => {
    document.getElementById("modalTitle").textContent = "添加用户";
    document.getElementById("userModal").classList.remove("hidden");
    document.getElementById("userModal").classList.add("flex");
  };
  document.getElementById("cancelUserBtn").onclick = closeModal;
  document.getElementById("saveUserBtn").onclick = saveUser;
}

function closeModal() {
  document.getElementById("userModal").classList.add("hidden");
  document.getElementById("userModal").classList.remove("flex");
}

async function loadUserList() {
  try {
    const list = await api("/api/users");
    document.getElementById("userList").innerHTML = list.map(u => `
      <div class="bg-white rounded-xl border p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">${u.display_name[0]}</div>
        <div class="flex-1">
          <div class="font-medium">${u.display_name} <span class="text-xs text-slate-400 ml-2">@${u.username}</span></div>
          <div class="text-sm text-slate-500">${u.department || "未分配部门"} · ${u.role_name}</div>
        </div>
        <button onclick="resetPwd(${u.id}, '${u.username}')" class="text-xs bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg">重置密码</button>
        <button onclick="delUser(${u.id}, '${u.display_name}')" class="text-xs bg-red-50 hover:bg-red-100 text-red-600 px-3 py-1.5 rounded-lg">删除</button>
      </div>`).join("");
  } catch(e) { alert(e.message); }
}

async function saveUser() {
  const name = document.getElementById("userName").value.trim();
  const account = document.getElementById("userAccount").value.trim();
  const pwd = document.getElementById("userPwd").value;
  const role = document.getElementById("userRole").value;
  const dept = document.getElementById("userDept").value.trim();
  if (!name || !account || !pwd) { alert("请填完整"); return; }
  try {
    await api("/api/users", {method:"POST", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({username: account, password: pwd, display_name: name, role: role, department: dept})});
    closeModal();
    loadUserList();
  } catch(e) { alert(e.message); }
}

async function resetPwd(id, name) {
  const pwd = prompt(`给 ${name} 设置新密码：`);
  if (!pwd) return;
  try {
    await api(`/api/users/${id}/reset-password`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({new_password: pwd})});
    alert("密码已重置");
  } catch(e) { alert(e.message); }
}

async function delUser(id, name) {
  if (!confirm(`确定删除 ${name}？`)) return;
  try {
    await api(`/api/users/${id}`, {method:"DELETE"});
    loadUserList();
  } catch(e) { alert(e.message); }
}"""

content = content.replace(old_rules_end, new_rules_end)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
