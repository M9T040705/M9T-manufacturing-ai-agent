"""把前端改成投产版"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 去掉外网CDN，换成本地文件
old_cdn = '<script src="https://cdn.tailwindcss.com"></script>'
new_cdn = '<script src="/static/css/tailwind.js"></script>'
content = content.replace(old_cdn, new_cdn)

# 2. 去掉demo提示（测试账号那行）
old_demo = """        <div class="mt-4 text-xs text-slate-400 text-center">
          测试账号：finance/fin123 · prod/prod123 · admin/admin123
        </div>"""
new_demo = ""
content = content.replace(old_demo, new_demo)

# 3. 登录页改更专业
old_login = """        <div class="text-center mb-6">
          <div class="text-4xl mb-3">🏭</div>
          <h1 class="text-xl font-bold text-slate-800">制造业AI Agent</h1>
          <p class="text-sm text-slate-500 mt-1">请登录</p>
        </div>"""
new_login = """        <div class="text-center mb-6">
          <div class="text-3xl font-bold text-blue-600">FDE</div>
          <p class="text-xs text-slate-400 mt-1">工厂数字员工平台</p>
          <div class="w-12 h-1 bg-blue-600 rounded-full mx-auto mt-3"></div>
        </div>"""
content = content.replace(old_login, new_login)

# 4. 加统一加载状态（全局）
old_style = """  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }"""
new_style = """  body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; }
  .loading { opacity: 0.6; pointer-events: none; }
  .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid #e2e8f0; border-top-color: #2563eb; border-radius: 50%; animation: spin 0.8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .toast { position: fixed; top: 20px; right: 20px; padding: 12px 20px; border-radius: 8px; color: white; z-index: 9999; animation: slideIn 0.3s ease; }
  @keyframes slideIn { from { transform: translateX(100px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }"""
content = content.replace(old_style, new_style)

# 5. 加toast工具函数
old_api = """async function api(path, opts={}) {
  opts.headers = opts.headers || {};
  if (token) opts.headers["Authorization"] = "Bearer " + token;
  const r = await fetch(path, opts);
  if (r.status === 401) { doLogout(); throw new Error("未登录"); }
  if (!r.ok) { const err = await r.json().catch(()=>({detail: r.statusText})); throw new Error(err.detail || "请求失败"); }
  return r.json();
}"""
new_api = """async function api(path, opts={}) {
  opts.headers = opts.headers || {};
  if (token) opts.headers["Authorization"] = "Bearer " + token;
  const r = await fetch(path, opts);
  if (r.status === 401) { doLogout(); throw new Error("未登录"); }
  if (!r.ok) { const err = await r.json().catch(()=>({detail: r.statusText})); throw new Error(err.detail || "请求失败"); }
  return r.json();
}

function toast(msg, type="success") {
  const colors = { success: "#16a34a", error: "#dc2626", warning: "#d97706" };
  const el = document.createElement("div");
  el.className = "toast";
  el.style.background = colors[type] || colors.success;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}"""
content = content.replace(old_api, new_api)

# 6. 登录按钮加loading状态
old_loginbtn = """document.getElementById("loginBtn").onclick = doLogin;"""
new_loginbtn = """document.getElementById("loginBtn").onclick = async () => {
  const btn = document.getElementById("loginBtn");
  btn.classList.add("loading");
  btn.innerHTML = '<span class="spinner"></span> 登录中...';
  await doLogin();
  btn.classList.remove("loading");
  btn.textContent = "登录";
};"""
content = content.replace(old_loginbtn, new_loginbtn)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
