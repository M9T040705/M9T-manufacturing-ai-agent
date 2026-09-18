"""升级自进化前端页面"""
path = r"E:\FDE项目\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换renderEvolutionPage
old_render = '''function renderEvolutionPage() {
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
}'''

new_render = '''function renderEvolutionPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">🔄 自进化中心</h1>
      <p class="text-sm text-slate-500 mt-1">反馈学习 → 自动归纳规则 → 回测验证 → 越用越准</p>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="evoCards" class="grid grid-cols-4 gap-4 mb-6"></div>

      <!-- Level 2: 自动规则归纳 -->
      <div class="bg-white rounded-xl border p-5 mb-4">
        <div class="flex items-center justify-between mb-3">
          <div class="font-medium text-slate-800">🤖 自动规则建议（Level 2）</div>
          <div class="text-xs text-slate-400">系统自动从反馈中归纳</div>
        </div>
        <div id="ruleSuggestions" class="space-y-3"></div>
      </div>

      <!-- 优化建议 -->
      <div class="bg-white rounded-xl border p-5 mb-4">
        <div class="font-medium text-slate-800 mb-3">💡 优化建议</div>
        <div id="evoSuggestions" class="space-y-2"></div>
      </div>

      <!-- 系统成熟度 -->
      <div class="bg-white rounded-xl border p-5">
        <div class="font-medium text-slate-800 mb-3">📈 系统成熟度</div>
        <div id="evoMaturity" class="text-sm text-slate-600"></div>
      </div>
    </div>`;
}'''

content = content.replace(old_render, new_render)

# 2. 替换bindEvolutionEvents
old_bind = '''async function bindEvolutionEvents() {
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
}'''

new_bind = '''async function bindEvolutionEvents() {
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

    // Level 2: 自动规则建议
    if (r.rule_suggestions && r.rule_suggestions.length) {
      document.getElementById("ruleSuggestions").innerHTML = r.rule_suggestions.map((s, i) => `
        <div class="border rounded-lg p-4 border-blue-200 bg-blue-50">
          <div class="flex items-center justify-between">
            <div class="font-medium">${s.title}</div>
            <span class="text-xs px-2 py-0.5 rounded-full ${s.priority==='high'?'bg-red-100 text-red-700':'bg-amber-100 text-amber-700'}">${s.priority==='high'?'高优先级':'中优先级'}</span>
          </div>
          <div class="text-sm text-slate-600 mt-2 whitespace-pre-line">${s.content}</div>
          <div class="text-xs text-slate-500 mt-2">原因：${s.reason}</div>
          <div class="text-xs text-green-600 mt-1">预计效果：${s.estimated_improvement}</div>
          <div class="flex gap-2 mt-3">
            <button onclick="testRuleSuggestion(${i})" class="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg">回测验证</button>
            <button class="text-xs bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg">采纳上线</button>
          </div>
          <div id="testResult_${i}" class="mt-3"></div>
        </div>`).join("");
    } else {
      document.getElementById("ruleSuggestions").innerHTML = `<div class="text-center text-slate-400 py-4">反馈数据不足，暂无法自动归纳规则</div>`;
    }

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
}

async function testRuleSuggestion(index) {
  try {
    // 先获取规则建议数据
    const r = await api("/api/evolution/report");
    const s = r.rule_suggestions[index];

    const result = await api("/api/evolution/test-rule", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(s)
    });

    const el = document.getElementById(`testResult_${index}`);
    el.innerHTML = `
      <div class="border rounded-lg p-3 bg-white">
        <div class="font-medium text-sm mb-2">📊 回测结果（Level 3）</div>
        <div class="grid grid-cols-3 gap-2 text-sm">
          <div>旧规则准确率：<span class="font-bold">${result.old_accuracy}</span></div>
          <div>新规则准确率：<span class="font-bold text-green-600">${result.new_accuracy}</span></div>
          <div>提升：<span class="font-bold text-green-600">${result.improvement}</span></div>
        </div>
        <div class="text-xs text-slate-500 mt-2">测试了${result.test_cases}条历史对话，多答对${result.detail.fixed_errors}条</div>
        <div class="text-xs mt-2 ${result.passed ? 'text-green-600' : 'text-red-600'}">结论：${result.conclusion}</div>
      </div>`;
  } catch(e) { toast(e.message, "error"); }
}'''

content = content.replace(old_bind, new_bind)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
