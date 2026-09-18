"""加前端数据治理+自进化页面"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 侧边栏加入口
old_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="models"><span>🧠</span> 模型配置</a>`;
  }"""
new_sidebar = """    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="models"><span>🧠</span> 模型配置</a>`;
    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="governance"><span>📊</span> 数据治理</a>`;
    if (currentUser.role === "admin") navHtml += `<a href="#" class="sidebar-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-600 hover:bg-slate-50" data-page="evolution"><span>🔄</span> 自进化</a>`;
  }"""
content = content.replace(old_sidebar, new_sidebar)

# 2. renderMain加路由
old_render = """  else if (currentPage === "models") main.innerHTML = renderModelsPage();"""
new_render = """  else if (currentPage === "models") main.innerHTML = renderModelsPage();
  else if (currentPage === "governance") main.innerHTML = renderGovernancePage();
  else if (currentPage === "evolution") main.innerHTML = renderEvolutionPage();"""
content = content.replace(old_render, new_render)

# 3. bind加路由
old_bind = """  else if (currentPage === "models") bindModelsEvents();"""
new_bind = """  else if (currentPage === "models") bindModelsEvents();
  else if (currentPage === "governance") bindGovernanceEvents();
  else if (currentPage === "evolution") bindEvolutionEvents();"""
content = content.replace(old_bind, new_bind)

# 4. 加页面（在changeLevel函数后面）
old_changemodel = """async function changeLevel(scene, level) {
  try {
    await api(`/api/model-config/${scene}`, {method:"PUT", headers:{"Content-Type":"application/json"},
      body: JSON.stringify({model_level: level})});
    bindModelsEvents();
  } catch(e) { alert(e.message); }
}"""

new_changemodel = old_changemodel + """

function renderGovernancePage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">📊 数据治理</h1>
      <p class="text-sm text-slate-500 mt-1">FDE第二层：数据质量 + 字典统一 + 血缘追踪</p>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="govCards" class="grid grid-cols-3 gap-4 mb-6"></div>
      <div class="bg-white rounded-xl border p-5 mb-4">
        <div class="font-medium text-slate-800 mb-3">⚠️ 数据质量问题</div>
        <div id="govIssues" class="space-y-2"></div>
      </div>
      <div class="bg-white rounded-xl border p-5">
        <div class="font-medium text-slate-800 mb-3">🔗 数据血缘</div>
        <div id="govLineage" class="space-y-2 text-sm text-slate-600"></div>
      </div>
    </div>`;
}

async function bindGovernanceEvents() {
  try {
    const r = await api("/api/governance/report");
    document.getElementById("govCards").innerHTML = `
      <div class="border rounded-xl p-4 ${r.high > 0 ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}">
        <div class="text-sm text-slate-500">高优先级问题</div>
        <div class="text-2xl font-bold ${r.high > 0 ? 'text-red-600' : 'text-green-600'}">${r.high}</div>
      </div>
      <div class="border rounded-xl p-4 ${r.medium > 0 ? 'bg-amber-50 border-amber-200' : 'bg-green-50 border-green-200'}">
        <div class="text-sm text-slate-500">中优先级问题</div>
        <div class="text-2xl font-bold ${r.medium > 0 ? 'text-amber-600' : 'text-green-600'}">${r.medium}</div>
      </div>
      <div class="border rounded-xl p-4 bg-blue-50 border-blue-200">
        <div class="text-sm text-slate-500">血缘记录</div>
        <div class="text-2xl font-bold text-blue-600">${r.lineage.length}</div>
      </div>`;

    if (r.issues.length) {
      document.getElementById("govIssues").innerHTML = r.issues.map(i => `
        <div class="border rounded-lg p-3 ${i.severity==='high'?'border-red-200 bg-red-50':i.severity==='medium'?'border-amber-200 bg-amber-50':'border-slate-200'}">
          <span class="text-xs px-2 py-0.5 rounded-full ${i.severity==='high'?'bg-red-200 text-red-800':i.severity==='medium'?'bg-amber-200 text-amber-800':'bg-slate-200 text-slate-600'}">${i.severity}</span>
          <span class="text-sm ml-2">${i.message}</span>
        </div>`).join("");
    } else {
      document.getElementById("govIssues").innerHTML = `<div class="text-center text-green-600 py-4">✅ 数据质量良好，无问题</div>`;
    }

    if (r.lineage.length) {
      document.getElementById("govLineage").innerHTML = r.lineage.map(l => `
        <div class="border rounded-lg p-3">
          <div><strong>${l.source}</strong> — ${l.rows}行数据</div>
          <div class="text-xs text-slate-400 mt-1">原始字段：${l.fields.join("、")}</div>
          <div class="text-xs text-slate-400">标准化后：${l.normalized_fields.join("、")}</div>
        </div>`).join("");
    } else {
      document.getElementById("govLineage").innerHTML = `<div class="text-slate-400">暂无血缘记录（取数后自动记录）</div>`;
    }
  } catch(e) { alert(e.message); }
}

function renderEvolutionPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">🔄 自进化</h1>
      <p class="text-sm text-slate-500 mt-1">FDE第五层：反馈学习 → 规则优化 → 越用越准</p>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="evoCards" class="grid grid-cols-4 gap-4 mb-6"></div>
      <div class="bg-white rounded-xl border p-5 mb-4">
        <div class="font-medium text-slate-800 mb-3">💡 优化建议</div>
        <div id="evoSuggestions" class="space-y-2"></div>
      </div>
      <div class="bg-white rounded-xl border p-5">
        <div class="font-medium text-slate-800 mb-3">📈 系统成熟度</div>
        <div id="evoMaturity" class="text-sm text-slate-600"></div>
      </div>
    </div>`;
}

async function bindEvolutionEvents() {
  try {
    const r = await api("/api/evolution/report");
    const m = r.metrics;
    document.getElementById("evoCards").innerHTML = `
      <div class="border rounded-xl p-4 bg-blue-50 border-blue-200">
        <div class="text-sm text-slate-500">总反馈数</div>
        <div class="text-2xl font-bold text-blue-600">${m.total_feedback}</div>
      </div>
      <div class="border rounded-xl p-4 bg-green-50 border-green-200">
        <div class="text-sm text-slate-500">👍 好评</div>
        <div class="text-2xl font-bold text-green-600">${m.good_count}</div>
      </div>
      <div class="border rounded-xl p-4 bg-red-50 border-red-200">
        <div class="text-sm text-slate-500">👎 差评</div>
        <div class="text-2xl font-bold text-red-600">${m.bad_count}</div>
      </div>
      <div class="border rounded-xl p-4 bg-purple-50 border-purple-200">
        <div class="text-sm text-slate-500">满意度</div>
        <div class="text-2xl font-bold text-purple-600">${(m.satisfaction_rate*100).toFixed(0)}%</div>
      </div>`;

    if (r.suggestions.length) {
      document.getElementById("evoSuggestions").innerHTML = r.suggestions.map(s => `
        <div class="border rounded-lg p-3 ${s.severity==='high'?'border-red-200 bg-red-50':s.severity==='low'?'border-green-200 bg-green-50':'border-amber-200 bg-amber-50'}">
          <div class="font-medium">${s.message}</div>
          <div class="text-sm text-slate-600 mt-1">👉 ${s.action}</div>
        </div>`).join("");
    } else {
      document.getElementById("evoSuggestions").innerHTML = `<div class="text-center text-slate-400 py-4">暂无建议</div>`;
    }

    document.getElementById("evoMaturity").innerHTML = `
      <div class="text-lg font-bold">${m.maturity}</div>
      <div class="text-sm text-slate-500 mt-1">${m.maturity_desc}</div>
      <div class="text-xs text-slate-400 mt-2">能自进化：${m.can_self_evolve ? '✅ 是' : '❌ 反馈数据不足'}</div>`;
  } catch(e) { alert(e.message); }
}"""

content = content.replace(old_changemodel, new_changemodel)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
