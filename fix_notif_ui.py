"""改前端通知页面，加已读功能"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 替换renderNotificationsPage
old_render = '''function renderNotificationsPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4">
      <h1 class="text-xl font-bold text-slate-800">🔔 消息通知</h1>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="notifList" class="space-y-3 max-w-2xl"></div>
    </div>`;
}'''

new_render = '''function renderNotificationsPage() {
  return `
    <header class="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">🔔 消息通知</h1>
      </div>
      <button id="readAllBtn" class="text-sm text-blue-600 hover:underline">全部标为已读</button>
    </header>
    <div class="flex-1 overflow-y-auto p-8">
      <div id="notifList" class="space-y-3 max-w-2xl"></div>
    </div>`;
}'''

content = content.replace(old_render, new_render)

# 替换bindNotificationsEvents
old_bind = '''async function bindNotificationsEvents() {
  try {
    const list = await api("/api/notifications");
    const el = document.getElementById("notifList");
    if (!list.length) { el.innerHTML = `<div class="text-center text-slate-400 py-20">✅ 暂无通知</div>`; return; }
    el.innerHTML = list.map(n => {
      const color = n.type === "alarm" ? "red" : (n.type === "approval" ? "amber" : "blue");
      const bg = color === "red" ? "border-red-200 bg-red-50" : (color === "amber" ? "border-amber-200 bg-amber-50" : "border-blue-200 bg-blue-50");
      return `<div class="border rounded-xl p-4 ${bg}">
        <div class="font-medium">${n.title}</div>
        <div class="text-sm text-slate-600 mt-1">${n.desc}</div>
        <div class="text-xs text-slate-400 mt-1">${n.time}</div>
      </div>`;
    }).join("");
  } catch(e) {}
}'''

new_bind = '''async function bindNotificationsEvents() {
  await loadNotifList();
  document.getElementById("readAllBtn").onclick = async () => {
    await api("/api/notifications/read-all", {method:"POST"});
    loadNotifList();
    updateNotifBadge();
  };
}

async function loadNotifList() {
  try {
    const list = await api("/api/notifications");
    const el = document.getElementById("notifList");
    if (!list.length) { el.innerHTML = `<div class="text-center text-slate-400 py-20">✅ 暂无通知</div>`; return; }
    el.innerHTML = list.map(n => {
      const color = n.type === "alarm" ? "red" : (n.type === "approval" ? "amber" : "blue");
      const bg = color === "red" ? "border-red-200" : (color === "amber" ? "border-amber-200" : "border-blue-200");
      const opacity = n.read ? "opacity-60 bg-slate-50" : "bg-white";
      return `<div class="border rounded-xl p-4 ${bg} ${opacity} cursor-pointer hover:shadow-sm" onclick="markOneRead('${n.id}')">
        <div class="flex items-center justify-between">
          <div class="font-medium">${n.title} ${n.read ? '<span class="text-xs text-slate-400 font-normal">已读</span>' : '<span class="text-xs text-blue-500 font-normal">未读</span>'}</div>
          ${n.read ? "" : '<div class="w-2 h-2 rounded-full bg-blue-500"></div>'}
        </div>
        <div class="text-sm text-slate-600 mt-1">${n.desc}</div>
        <div class="text-xs text-slate-400 mt-1">${n.time}</div>
      </div>`;
    }).join("");
  } catch(e) {}
}

async function markOneRead(id) {
  await api(`/api/notifications/${id}/read`, {method:"POST"});
  loadNotifList();
  updateNotifBadge();
}'''

content = content.replace(old_bind, new_bind)

# 改updateNotifBadge，显示未读数量
old_badge = '''async function updateNotifBadge() {
  try {
    const list = await api("/api/notifications");
    const badge = document.getElementById("notifBadge");
    if (!badge) return;
    if (list.length > 0) {
      badge.textContent = list.length;
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  } catch(e) {}
}'''

new_badge = '''async function updateNotifBadge() {
  try {
    const list = await api("/api/notifications");
    const unread = list.filter(n => !n.read).length;
    const badge = document.getElementById("notifBadge");
    if (!badge) return;
    if (unread > 0) {
      badge.textContent = unread;
      badge.classList.remove("hidden");
    } else {
      badge.classList.add("hidden");
    }
  } catch(e) {}
}'''

content = content.replace(old_badge, new_badge)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
