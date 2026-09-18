"""给前端加模型配置管理页面"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 侧边栏加入口
old_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="users"><span>👥</span> 用户管理</a>`;
  }"""
new_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="users"><span>👥</span> 用户管理</a>`;
    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="models"><span>🧠</span> 模型配置</a>`;
  }"""
content = content.replace(old_sidebar, new_sidebar)

# 2. renderMain加路由
old_render = """  else if (currentPage === "users") main.innerHTML = renderUsersPage();"""
new_render = """  else if (currentPage === "users") main.innerHTML = renderUsersPage();
  else if (currentPage === "models") main.innerHTML = renderModelsPage();"""
content = content.replace(old_render, new_render)

# 3. bind加路由
old_bind = """  else if (currentPage === "users") bindUsersEvents();"""
new_bind = """  else if (currentPage === "users") bindUsersEvents();
  else if (currentPage === "models") bindModelsEvents();"""
content = content.replace(old_bind, new_bind)

# 4. 加模型配置页面（在delUser函数后面）
old_deluser = """async function delUser(id, name) {
  if (!confirm(`确定删除 ${name}？`)) return;
  try {
    await api(`/api/users/${id}`, {method:"DELETE"});
    loadUserList();
  } catch(e) { alert(e.message); }
}"""

new_deluser = old_deluser + """

function renderModelsPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">🧠 模型配置</h1>
      <p class="text-sm text-slate-500 mt-1">每个部门用不同等级的模型——简单任务用轻量模型省钱，复杂任务用重型模型保准</p>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="modelCards" class="grid grid-cols-2 gap-4 mb-6"></div>
      <div id="levelInfo" class="bg-white rounded-xl border p-5"></div>
    </div>`;
}

async function bindModelsEvents() {
  try {
    const list = await api("/api/model-config");
    document.getElementById("modelCards").innerHTML = list.map(m => {
      const levelColor = m.model_level === "heavy" ? "purple" : (m.model_level === "standard" ? "blue" : "green");
      const bg = levelColor === "purple" ? "bg-purple-50 border-purple-200" : (levelColor === "blue" ? "bg-blue-50 border-blue-200" : "bg-green-50 border-green-200");
      const text = levelColor === "purple" ? "text-purple-700" : (levelColor === "blue" ? "text-blue-700" : "text-green-700");
      return `<div class="border rounded-xl p-5 ${bg}">
        <div class="flex items-center justify-between mb-2">
          <div class="font-bold text-slate-800">${m.department || m.scene}</div>
          <span class="text-xs px-2 py-1 rounded-full bg-white ${text}">${m.level_name}</span>
        </div>
        <div class="text-sm text-slate-600 mb-3">${m.description}</div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-slate-500">模型等级：</label>
          <select onchange="changeLevel('${m.scene}', this.value)" class="text-sm border rounded-lg px-2 py-1 bg-white">
            <option value="light" ${m.model_level==='light'?'selected':''}>⚡ 轻量（快/便宜）</option>
            <option value="standard" ${m.model_level==='standard'?'selected':''}>⚖️ 标准（平衡）</option>
            <option value="heavy" ${m.model_level==='heavy'?'selected':''}>🧠 重型（准/贵）</option>
          </select>
          <span class="text-xs text-slate-400 ml-auto">${m.speed} · ${m.cost}</span>
        </div>
      </div>`;
    }).join("");

    // 模型等级说明
    const levels = await api("/api/model-levels");
    document.getElementById("levelInfo").innerHTML = `
      <div class="font-medium text-slate-800 mb-3">💡 模型等级说明</div>
      <div class="grid grid-cols-3 gap-4">
        ${Object.entries(levels).map(([k, v]) => `
          <div class="border rounded-lg p-3">
            <div class="font-medium">${v.name}</div>
            <div class="text-xs text-slate-500 mt-1">${v.description}</div>
            <div class="text-xs text-slate-400 mt-2">速度：${v.speed} · 成本：${v.cost}</div>
          </div>`).join("")}
      </div>`;
  } catch(e) { alert(e.message); }
}

async function changeLevel(scene, level) {
  try {
    await api(`/api/model-config/${scene}`, {method:"PUT", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({model_level: level})});
    bindModelsEvents();
  } catch(e) { alert(e.message); }
}"""

content = content.replace(old_deluser, new_deluser)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
