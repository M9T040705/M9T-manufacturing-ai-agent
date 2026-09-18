"""加前端运维管理页面"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 侧边栏加入口
old_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="evolution"><span>🔄</span> 自进化</a>`;
  }"""
new_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="evolution"><span>🔄</span> 自进化</a>`;
    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="ops"><span>🛠️</span> 运维管理</a>`;
  }"""
content = content.replace(old_sidebar, new_sidebar)

# 2. renderMain加路由
old_render = """  else if (currentPage === "settings") main.innerHTML = renderSettingsPage();"""
new_render = """  else if (currentPage === "settings") main.innerHTML = renderSettingsPage();
  else if (currentPage === "ops") main.innerHTML = renderOpsPage();"""
content = content.replace(old_render, new_render)

# 3. bind加路由
old_bind = """  else if (currentPage === "settings") bindSettingsEvents();"""
new_bind = """  else if (currentPage === "settings") bindSettingsEvents();
  else if (currentPage === "ops") bindOpsEvents();"""
content = content.replace(old_bind, new_bind)

# 4. 加运维页面
old_settings = """async function bindSettingsEvents() {"""
new_settings = '''function renderOpsPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">🛠️ 运维管理</h1>
      <p class="text-sm text-slate-500 mt-1">版本回退、数据备份、错误监控</p>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="opsStatus" class="grid grid-cols-3 gap-4 mb-6"></div>
      <div class="grid grid-cols-2 gap-4">
        <div class="bg-white rounded-xl border p-5">
          <div class="flex items-center justify-between mb-3">
            <div class="font-medium text-slate-800">💾 快照管理（版本回退）</div>
            <button onclick="createSnapshot()" class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-sm">创建快照</button>
          </div>
          <div id="snapshotList" class="space-y-2 max-h-64 overflow-y-auto"></div>
        </div>
        <div class="bg-white rounded-xl border p-5">
          <div class="flex items-center justify-between mb-3">
            <div class="font-medium text-slate-800">⚠️ 错误日志</div>
            <button onclick="refreshErrors()" class="text-sm text-blue-600 hover:underline">刷新</button>
          </div>
          <div id="errorList" class="space-y-2 max-h-64 overflow-y-auto"></div>
        </div>
      </div>
      <div class="mt-4 bg-white rounded-xl border p-5">
        <div class="font-medium text-slate-800 mb-3">💾 数据备份</div>
        <div class="flex gap-2">
          <button onclick="backupDb()" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm">备份数据库</button>
        </div>
      </div>
    </div>`;
}

async function bindOpsEvents() {
  try {
    const r = await api("/api/ops/status");
    document.getElementById("opsStatus").innerHTML = `
      <div class="border rounded-xl p-4 bg-blue-50 border-blue-200">
        <div class="text-sm text-slate-500">系统版本</div>
        <div class="text-xl font-bold text-blue-600">v${r.version}</div>
      </div>
      <div class="border rounded-xl p-4 bg-green-50 border-green-200">
        <div class="text-sm text-slate-500">运行时间</div>
        <div class="text-xl font-bold text-green-600">${r.uptime}</div>
      </div>
      <div class="border rounded-xl p-4 bg-amber-50 border-amber-200">
        <div class="text-sm text-slate-500">最近错误</div>
        <div class="text-xl font-bold text-amber-600">${r.recent_errors}条</div>
      </div>`;

    // 快照列表
    const snaps = await api("/api/ops/snapshots");
    if (snaps.length) {
      document.getElementById("snapshotList").innerHTML = snaps.map(s => `
        <div class="border rounded-lg p-3 flex items-center justify-between">
          <div>
            <div class="text-sm font-medium">${s.name}</div>
            <div class="text-xs text-slate-400">${s.time}</div>
          </div>
          <button onclick="rollback('${s.name}')" class="text-xs bg-amber-100 hover:bg-amber-200 px-3 py-1 rounded-lg">回退到此版本</button>
        </div>`).join("");
    } else {
      document.getElementById("snapshotList").innerHTML = `<div class="text-center text-slate-400 text-sm py-4">暂无快照</div>`;
    }

    // 错误日志
    await refreshErrors();
  } catch(e) { alert(e.message); }
}

async function refreshErrors() {
  try {
    const errors = await api("/api/ops/errors");
    if (errors.length) {
      document.getElementById("errorList").innerHTML = errors.map(e => `
        <div class="border rounded-lg p-3 border-red-200 bg-red-50">
          <div class="text-xs text-red-600">${e.component}</div>
          <div class="text-sm text-slate-700 mt-1">${e.error}</div>
          <div class="text-xs text-slate-400 mt-1">${e.time}</div>
        </div>`).join("");
    } else {
      document.getElementById("errorList").innerHTML = `<div class="text-center text-green-600 text-sm py-4">✅ 无错误</div>`;
    }
  } catch(e) {}
}

async function createSnapshot() {
  try {
    const r = await api("/api/ops/snapshot", {method:"POST"});
    toast("快照创建成功");
    bindOpsEvents();
  } catch(e) { toast(e.message, "error"); }
}

async function rollback(name) {
  if (!confirm(`确定回退到 ${name}？当前配置会被覆盖`)) return;
  try {
    const r = await api(`/api/ops/rollback/${name}`, {method:"POST"});
    toast("回退成功，请刷新页面");
    bindOpsEvents();
  } catch(e) { toast(e.message, "error"); }
}

async function backupDb() {
  try {
    const r = await api("/api/ops/backup", {method:"POST"});
    toast("数据库备份成功");
  } catch(e) { toast(e.message, "error"); }
}

async function bindSettingsEvents() {'''

content = content.replace(old_settings, new_settings)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
