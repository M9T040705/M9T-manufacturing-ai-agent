"""
工业AI Agent - FastAPI后端
"""
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_engine import AgentEngine
from core.data_connector import DataConnector
from core.knowledge_base import KnowledgeBase
from core.human_review import HumanReviewGate
from core.state_store import StateStore, ROLE_NAMES
from core.skill_loader import SkillRegistry
from core.model_router import ModelRouter
from core.data_governance import DataGovernance
from core.self_evolution import SelfEvolution
from core.ops_manager import OpsManager
from core import data_store
import secrets
from datetime import datetime

# ── 初始化 ──────────────────────────────────
app = FastAPI(title="制造业AI Agent平台")

engine = AgentEngine(
    connector=DataConnector(mode="auto"),
    kb=KnowledgeBase(),
    review_gate=HumanReviewGate(),
)
# 技能插件：从vault/skills/*.yaml加载（Harness式：一切皆插件）
skill_registry = SkillRegistry()
skill_registry.register_to_engine(engine)
state = StateStore()
model_router = ModelRouter()
data_governance = DataGovernance()
self_evolution = SelfEvolution(state)
ops = OpsManager()

# 简单内存token存储（MVP阶段，生产可换JWT）
_tokens: dict[str, dict] = {}

from fastapi import Request, Depends

async def get_current_user(request: Request) -> dict:
    """从header解析当前登录用户"""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    user = _tokens.get(token)
    if not user:
        from fastapi import HTTPException as HE
        raise HE(status_code=401, detail="未登录")
    return user


async def require_admin(request: Request) -> dict:
    """仅管理员可访问"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        from fastapi import HTTPException as HE
        raise HE(status_code=403, detail="仅管理员可访问")
    return user


# ── 请求模型 ─────────────────────────────────
class AskRequest(BaseModel):
    question: str
    user: str = "用户"

class LoginRequest(BaseModel):
    username: str
    password: str

# ── API路由 ─────────────────────────────────

# 登录失败计数（安全加固）
_login_failures: dict = {}
MAX_FAIL = 5
LOCK_TIME = 300  # 5分钟

@app.post("/api/login")
async def login(req: LoginRequest):
    """登录，返回token和用户信息"""
    from datetime import datetime
    now = datetime.now().timestamp()
    fails = _login_failures.get(req.username, {"count": 0, "lock_until": 0})
    if fails["lock_until"] > now:
        remain = int((fails["lock_until"] - now) / 60)
        raise HTTPException(429, f"失败次数过多，请{remain}分钟后再试")

    user = state.verify_user(req.username, req.password)
    if not user:
        fails["count"] += 1
        if fails["count"] >= MAX_FAIL:
            fails["lock_until"] = now + LOCK_TIME
            fails["count"] = 0
        _login_failures[req.username] = fails
        raise HTTPException(401, "用户名或密码错误")

    if req.username in _login_failures:
        del _login_failures[req.username]

    token = secrets.token_hex(16)
    user["token"] = token
    user["permissions"] = state.user_permissions(user["role"])
    user["role_name"] = ROLE_NAMES.get(user["role"], user["role"])
    _tokens[token] = user
    return user


@app.get("/api/me")
async def me(user: dict = Depends(get_current_user)):
    """当前用户信息和权限"""
    user["permissions"] = state.user_permissions(user["role"])
    user["role_name"] = ROLE_NAMES.get(user["role"], user["role"])
    return user


class ChangePwdRequest(BaseModel):
    old_password: str
    new_password: str

@app.post("/api/change-password")
async def change_password(req: ChangePwdRequest, user: dict = Depends(get_current_user)):
    """用户自己修改密码"""
    import hashlib
    old_hash = hashlib.sha256(req.old_password.encode()).hexdigest()
    # 验证旧密码
    if not state.verify_user(user["username"], req.old_password):
        raise HTTPException(400, "旧密码不正确")
    # 更新密码
    state.reset_password(user["id"], req.new_password)
    return {"status": "ok", "message": "密码修改成功"}

@app.post("/api/logout")
async def logout(request: Request, user: dict = Depends(get_current_user)):
    """退出登录，token失效"""
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "") if auth.startswith("Bearer ") else ""
    if token in _tokens:
        del _tokens[token]
    return {"status": "ok"}

@app.get("/api/health")
async def health():
    """系统健康检查"""
    import os
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": state.mode,
        "llm_enabled": engine.llm.enabled,
        "uptime": "running",
    }

@app.delete("/api/upload/{table_key}")
async def delete_upload(table_key: str, user: dict = Depends(require_admin)):
    """删除上传的数据表（管理员）"""
    from core import data_store
    try:
        data_store.delete_table(table_key)
        return {"status": "ok", "message": "已删除，恢复示例数据"}
    except Exception as e:
        raise HTTPException(400, f"删除失败: {str(e)}")


@app.post("/api/ask")
async def ask(req: AskRequest, user: dict = Depends(get_current_user)):
    """提交问题，Agent跑一遍返回结果"""
    resp = engine.ask(req.question, user["display_name"])
    scene_map = {
        "procurement_reconciliation": "reconciliation",
        "delivery_quotation": "delivery",
        "daily_briefing": "daily",
        "material_kitting": "kitting",
        "equipment_maintenance": "equipment",
        "quality_traceability": "quality",
    }
    scene = scene_map.get(resp.intent, "general")
    # 权限校验：这个用户能不能访问这个场景
    allowed_scenes = state.user_permissions(user["role"])["scenes"]
    if scene not in allowed_scenes and user["role"] != "admin":
        resp.answer = f"⛔ 你没有权限访问「{scene}」场景。请联系管理员分配权限。"
    state.save_message(scene, "user", req.question, resp.intent)
    state.save_message(scene, "ai", resp.answer, resp.intent)
    # 自进化：查历史成功案例，附在回答后面
    good_examples = state.get_good_examples(scene, limit=1)
    extra = ""
    if good_examples:
        extra = f"\n\n💡 历史参考：之前类似问题的处理方式：\n{good_examples[0]['answer'][:200]}"
    return {
        "answer": resp.answer + extra,
        "intent": resp.intent,
        "steps": resp.steps_taken,
        "data_summary": resp.data_summary,
        "need_review": resp.need_human_review,
        "review": resp.review_request,
    }


@app.get("/api/history/{scene}")
async def get_history(scene: str):
    """获取某场景的对话历史"""
    return state.get_history(scene)


@app.get("/api/pending")
async def list_pending():
    """待审批列表"""
    pending = engine.review.pending_list()
    return [
        {
            "id": r.request_id,
            "action": r.action,
            "risk": r.risk_level.value,
            "approver": r.approver_role,
            "status": r.status.value,
        }
        for r in pending
    ]


@app.post("/api/approve/{request_id}")
async def approve(request_id: str, approver: str = "当前用户"):
    r = engine.review.approve(request_id, approver)
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "approved", "id": r.request_id}


@app.post("/api/reject/{request_id}")
async def reject(request_id: str, approver: str = "当前用户"):
    r = engine.review.reject(request_id, approver)
    if r is None:
        raise HTTPException(404, "审批单不存在")
    return {"status": "rejected", "id": r.request_id}


@app.get("/api/tables")
async def list_tables():
    """所有数据表状态"""
    uploaded = data_store.list_uploaded()
    tables = []
    for key, schema in data_store.TABLE_SCHEMAS.items():
        tables.append({
            "key": key,
            "description": schema["description"],
            "columns": schema["columns"],
            "uploaded": key in uploaded,
            "rows": uploaded.get(key, {}).get("rows", 0),
        })
    return tables


@app.get("/api/data-status")
async def data_status():
    """数据源接入状态总览：每个系统域接了几张表"""
    uploaded = data_store.list_uploaded()
    domains = [
        {"key": "ERP", "name": "ERP（订单/库存/采购/应付）", "entities": ["orders", "inventory", "purchase_orders", "ap_invoices"]},
        {"key": "MES", "name": "MES（工单/报工）", "entities": ["work_orders", "shift_records"]},
        {"key": "WMS", "name": "WMS（出入库/批次）", "entities": ["stock", "in_out"]},
        {"key": "QMS", "name": "QMS（检验/不良）", "entities": ["inspections", "defects"]},
        {"key": "PLM", "name": "PLM（BOM/工艺）", "entities": ["bom", "routing"]},
        {"key": "SCADA", "name": "SCADA（设备状态/报警）", "entities": ["equipment", "alarms"]},
    ]
    result = []
    for d in domains:
        entities = []
        real_count = 0
        for ent in d["entities"]:
            full_key = f"{d['key']}_{ent}"
            is_real = full_key in uploaded
            if is_real:
                real_count += 1
            entities.append({"name": ent, "is_real": is_real})
        result.append({
            "domain": d["key"], "name": d["name"],
            "total": len(d["entities"]), "real": real_count,
            "entities": entities,
        })
    return result


@app.post("/api/upload/{table_key}")
async def upload_table(table_key: str, file: UploadFile = File(...)):
    if table_key not in data_store.TABLE_SCHEMAS:
        raise HTTPException(400, f"未知表: {table_key}")
    content = await file.read()
    success, msg = data_store.save_uploaded(table_key, content, file.filename)
    if not success:
        raise HTTPException(400, msg)
    return {"message": msg, "table": table_key}


@app.get("/api/template/{table_key}")
async def download_template(table_key: str):
    from fastapi.responses import Response
    if table_key not in data_store.TABLE_SCHEMAS:
        raise HTTPException(400, "未知表")
    content = data_store.download_template(table_key)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={table_key}_template.csv"},
    )


@app.get("/api/audit")
async def list_audit():
    """审计日志列表"""
    audit_dir = Path(__file__).parent / "audit"
    files = sorted(audit_dir.glob("audit_*.json"), reverse=True)
    import json
    result = []
    for f in files[:20]:
        try:
            with open(f, encoding="utf-8") as fp:
                entries = json.load(fp)
            result.append({"file": f.name, "entries": entries})
        except:
            pass
    return result


# ── 问题模型（对应Ha7ch：先建问题再选场景）─────
class ProblemModelReq(BaseModel):
    bottleneck: str = ""
    causal_chain: str = ""
    impact: str = ""
    stakeholders: str = ""
    previous_attempt: str = ""


@app.get("/api/problem-model")
async def get_problem_model():
    return state.get_problem_model() or {"bottleneck": "", "causal_chain": "", "impact": "", "stakeholders": "", "previous_attempt": ""}


@app.post("/api/problem-model")
async def save_problem_model(req: ProblemModelReq):
    state.save_problem_model(req.bottleneck, req.causal_chain, req.impact, req.stakeholders, req.previous_attempt)
    return {"status": "saved"}


# ── 智能诊断：用户说痛点，自动推荐场景 ─────
class DiagnoseReq(BaseModel):
    description: str

SCENE_KEYWORDS = {
    "reconciliation": {
        "keywords": ["对账", "发票", "付款", "财务", "采购单", "收货", "应付", "三单"],
        "title": "采购三单匹配对账",
        "reason": "你提到对账/财务相关，说明采购单/收货单/发票核对耗时长、容易出错。",
        "value": "自动核对三单，差异自动标红，财务对账从5人天降到1人天。",
    },
    "delivery": {
        "keywords": ["交期", "交货", "什么时候能出", "客户催", "交不出", "延期", "承诺"],
        "title": "销售交期答复",
        "reason": "你提到交期问题，说明销售答复客户要问很多人、来回确认慢。",
        "value": "5分钟给出建议交期+风险提示，减少销售和客户之间的来回沟通。",
    },
    "daily": {
        "keywords": ["日报", "每天看", "老板", "异常", "盯什么", "每天问", "看不到"],
        "title": "管理每日一页",
        "reason": "你提到管理视角的问题，说明老板每天要逐个部门问才知道工厂状况。",
        "value": "每天自动汇总全厂异常一页纸，老板5分钟掌握全局。",
    },
    "kitting": {
        "keywords": ["缺料", "齐套", "物料", "库存不够", "停线", "欠料", "BOM"],
        "title": "生产齐套欠料",
        "reason": "你提到物料/缺料问题，说明经常因为缺料导致停线或延期。",
        "value": "提前算缺口，缺料预警提前几天知道，减少非计划停线。",
    },
    "equipment": {
        "keywords": ["设备", "停机", "报警", "维修", "保养", "点检", "故障", "CNC"],
        "title": "设备点检维保",
        "reason": "你提到设备问题，说明设备故障被动响应、维修靠老师傅经验。",
        "value": "报警自动汇总+维修经验建议，减少非计划停机。",
    },
    "quality": {
        "keywords": ["质量", "客诉", "不良", "追溯", "批次", "不合格", "召回", "判责"],
        "title": "质量批次追溯",
        "reason": "你提到质量问题，说明客诉追溯慢、根因分析靠猜。",
        "value": "批次全链路追溯从3天缩到4小时，根因自动关联设备/人员/班次。",
    },
}


@app.post("/api/diagnose")
async def diagnose(req: DiagnoseReq):
    """用户说一段话，分析痛点，推荐先做哪个场景"""
    text = req.description
    scores = []
    for scene_id, rule in SCENE_KEYWORDS.items():
        hits = sum(1 for kw in rule["keywords"] if kw in text)
        if hits > 0:
            scores.append({"scene": scene_id, "score": hits, "rule": rule})
    scores.sort(key=lambda x: -x["score"])

    if not scores:
        return {
            "recommendation": None,
            "alternatives": [],
            "message": "没识别到明确痛点。你可以说说：工厂哪个环节最耗人、最容易出错、最影响交期？",
        }

    top = scores[0]
    rec = {
        "scene": top["scene"],
        "title": top["rule"]["title"],
        "reason": top["rule"]["reason"],
        "value": top["rule"]["value"],
    }
    alternatives = [{"scene": s["scene"], "title": s["rule"]["title"]} for s in scores[1:3]]

    state.save_problem_model(
        bottleneck=text[:200], causal_chain="", impact="", stakeholders="", previous_attempt="",
    )

    return {
        "recommendation": rec,
        "alternatives": alternatives,
        "message": f"基于你说的，建议先做「{top['rule']['title']}」",
    }


# ── 知识规则管理 ─────────────────────────────
@app.get("/api/rules")
async def list_rules():
    """列出所有规则及其版本"""
    return engine.kb.list_rules()


@app.get("/api/skills")
async def list_skills():
    """列出所有技能插件（从yaml加载）"""
    return skill_registry.list_all()


@app.post("/api/skills/reload")
async def reload_skills():
    """重新加载技能插件"""
    skill_registry.reload()
    skill_registry.register_to_engine(engine)
    return {"status": "reloaded", "count": len(skill_registry.skills)}


# ── 用户反馈（自进化）──────────────────────
class FeedbackReq(BaseModel):
    scene: str
    question: str
    answer: str
    rating: str
    comment: str = ""


@app.post("/api/feedback")
async def save_feedback(req: FeedbackReq, user: dict = Depends(get_current_user)):
    """用户对回答的反馈：👍有用 / 👎没用"""
    state.save_feedback(req.scene, req.question, req.answer, req.rating, req.comment, user["display_name"])
    return {"status": "saved"}


@app.get("/api/feedback/stats")
async def feedback_stats(user: dict = Depends(get_current_user)):
    """反馈统计"""
    return state.get_feedback_stats()


@app.get("/api/equipment/status")
async def equipment_status(user: dict = Depends(get_current_user)):
    """设备状态看板：全厂设备红绿黄（增量更新：只标变化的设备）"""
    conn = engine.connector
    machines = conn.query_scada("equipment")
    alarms = conn.query_scada("alarms")

    # 【优化5】增量更新：对比上次快照，只标变化的设备
    prev = engine._last_equip_snapshot
    changed = []
    for m in machines:
        mid = m["equip_id"]
        old = prev.get(mid)
        if not old or old.get("status") != m.get("status") or old.get("alarm") != m.get("alarm"):
            changed.append(mid)
        m["changed"] = mid in changed
    engine._last_equip_snapshot = {m["equip_id"]: m for m in machines}

    return {"machines": machines, "active_alarms": alarms, "changed_count": len(changed)}


@app.get("/api/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    """厂长首页看板：全厂KPI总览"""
    conn = engine.connector
    orders = conn.query_erp("orders")
    wo = conn.query_mes("work_orders")
    done = sum(1 for w in wo if w["status"] == "完工")
    order_rate = round(done / max(len(wo), 1) * 100, 1)
    machines = conn.query_scada("equipment")
    running = sum(1 for m in machines if m["status"] == "运行")
    equip_rate = round(running / max(len(machines), 1) * 100, 1)
    alarm_count = sum(1 for m in machines if m["status"] == "报警")
    inspections = conn.query_qms("inspections")
    passed = sum(1 for i in inspections if i["result"] == "合格")
    quality_rate = round(passed / max(len(inspections), 1) * 100, 1)
    inventory = conn.query_erp("inventory")
    low_stock = [i for i in inventory if i["stock_qty"] < i["safety_stock"]]
    pending = engine.review.pending_list()
    return {
        "order_completion_rate": order_rate,
        "order_total": len(orders),
        "equip_running_rate": equip_rate,
        "alarm_count": alarm_count,
        "quality_pass_rate": quality_rate,
        "low_stock_count": len(low_stock),
        "pending_approval": len(pending),
    }


@app.get("/api/notifications")
async def notifications(user: dict = Depends(get_current_user)):
    """消息通知列表（带已读状态）"""
    import hashlib
    conn = engine.connector
    raw = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            title = f"{m['equip_id']} 报警"
            desc = ", ".join(m.get("alarm", []))
            raw.append({"type": "alarm", "title": title, "desc": desc, "time": "现在"})
    pending = engine.review.pending_list()
    for p in pending:
        title = f"待审批：{p.action}"
        desc = f"需{p.approver_role}审批"
        raw.append({"type": "approval", "title": title, "desc": desc, "time": "现在"})
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            title = f"库存预警：{i['material']}"
            desc = f"库存{i['stock_qty']}{i['unit']}，低于安全线{i['safety_stock']}"
            raw.append({"type": "warning", "title": title, "desc": desc, "time": "现在"})
    # 给每条通知生成唯一ID（基于内容hash）
    for n in raw:
        n["id"] = hashlib.md5(f"{n['type']}{n['title']}{n['desc']}".encode()).hexdigest()[:12]
    # 查已读状态
    read_set = state.get_read_notifs(user["username"])
    for n in raw:
        n["read"] = n["id"] in read_set
    # 未读排前面
    raw.sort(key=lambda x: x["read"])
    return raw


@app.post("/api/notifications/{notif_id}/read")
async def mark_notif_read(notif_id: str, user: dict = Depends(get_current_user)):
    """标记单条通知为已读"""
    state.mark_notif_read(notif_id, user["username"])
    return {"status": "ok"}


@app.post("/api/notifications/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """标记所有通知为已读"""
    import hashlib
    conn = engine.connector
    raw = []
    machines = conn.query_scada("equipment")
    for m in machines:
        if m["status"] == "报警":
            title = f"{m['equip_id']} 报警"
            desc = ", ".join(m.get("alarm", []))
            raw.append(("alarm", title, desc))
    pending = engine.review.pending_list()
    for p in pending:
        title = f"待审批：{p.action}"
        desc = f"需{p.approver_role}审批"
        raw.append(("approval", title, desc))
    inventory = conn.query_erp("inventory")
    for i in inventory:
        if i["stock_qty"] < i["safety_stock"]:
            title = f"库存预警：{i['material']}"
            desc = f"库存{i['stock_qty']}{i['unit']}，低于安全线{i['safety_stock']}"
            raw.append(("warning", title, desc))
    marked = 0
    for typ, title, desc in raw:
        nid = hashlib.md5(f"{typ}{title}{desc}".encode()).hexdigest()[:12]
        state.mark_notif_read(nid, user["username"])
        marked += 1
    return {"status": "ok", "marked": marked}


@app.post("/api/export/{scene}")
async def export_report(scene: str, user: dict = Depends(get_current_user)):
    """导出报表CSV"""
    from fastapi.responses import Response
    conn = engine.connector
    data_map = {
        "reconciliation": lambda: conn.query_erp("purchase_orders"),
        "equipment": lambda: conn.query_scada("equipment"),
        "quality": lambda: conn.query_qms("inspections"),
        "delivery": lambda: conn.query_erp("orders"),
        "kitting": lambda: conn.query_erp("inventory"),
        "daily": lambda: conn.query_mes("work_orders"),
    }
    if scene not in data_map:
        raise HTTPException(400, "未知场景")
    data = data_map[scene]()
    if not data:
        csv = "无数据"
    else:
        keys = data[0].keys()
        csv = ",".join(keys) + "\n"
        for row in data:
            csv += ",".join(str(row.get(k, "")) for k in keys) + "\n"
    return Response(
        content=csv,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={scene}_report.csv"},
    )


@app.post("/api/kb/reload")
async def reload_kb():
    """重新加载vault知识库"""
    engine.kb.reload()
    return {"status": "reloaded", "rules": len(engine.kb.list_rules())}


# ── 用户管理（仅admin）────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    display_name: str
    role: str
    department: str = ""

class PasswordReset(BaseModel):
    new_password: str

@app.get("/api/users")
async def list_users(user = Depends(require_admin)):
    """列出所有用户（仅管理员）"""
    return state.list_users()

@app.post("/api/users")
async def create_user(req: UserCreate, user = Depends(require_admin)):
    """创建新用户（仅管理员）"""
    try:
        return state.create_user(req.username, req.password, req.display_name, req.role, req.department)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, user = Depends(require_admin)):
    """删除用户（仅管理员）"""
    state.delete_user(user_id)
    return {"status": "deleted"}

@app.post("/api/users/{user_id}/reset-password")
async def reset_password(user_id: int, req: PasswordReset, user = Depends(require_admin)):
    """重置密码（仅管理员）"""
    state.reset_password(user_id, req.new_password)
    return {"status": "reset"}

@app.get("/api/roles")
async def list_roles(user = Depends(require_admin)):
    """列出所有角色（仅管理员）"""
    return state.list_roles()


# ── 模型路由配置（仅admin）────────────────
@app.get("/api/model-config")
async def get_model_config(user = Depends(require_admin)):
    """列出所有场景的模型配置"""
    return model_router.list_scenes_config()

@app.put("/api/model-config/{scene}")
async def update_model_config(scene: str, req: dict, user = Depends(require_admin)):
    """更新某场景的模型等级"""
    new_level = req.get("model_level", "")
    ok = model_router.update_scene_level(scene, new_level)
    if not ok:
        raise HTTPException(status_code=400, detail="无效的模型等级或场景")
    return {"status": "ok", "scene": scene, "model_level": new_level}

@app.get("/api/model-levels")
async def get_model_levels(user = Depends(require_admin)):
    """列出所有模型等级"""
    return model_router._config.get("model_levels", {})

@app.get("/api/llm-status")
async def llm_status(user = Depends(get_current_user)):
    """大模型状态"""
    return engine.llm.get_status()


# ── 数据治理 + 自进化 API ──────────────────
@app.get("/api/governance/report")
async def governance_report(user = Depends(require_admin)):
    """数据质量报告（FDE第二层）"""
    return data_governance.get_quality_report()

@app.get("/api/evolution/report")
async def evolution_report(user = Depends(require_admin)):
    """自进化报告（FDE第五层）"""
    return self_evolution.get_full_report()


# ── 运维管理 API（仅admin）────────────────
@app.get("/api/ops/status")
async def ops_status(user = Depends(require_admin)):
    """系统运维状态"""
    return ops.get_system_status()

@app.get("/api/ops/snapshots")
async def list_snapshots(user = Depends(require_admin)):
    """列出所有快照"""
    return ops.list_snapshots()

@app.post("/api/ops/snapshot")
async def create_snapshot(user = Depends(require_admin)):
    """创建配置快照"""
    return ops.create_snapshot()

@app.post("/api/ops/rollback/{snapshot_name}")
async def rollback(snapshot_name: str, user = Depends(require_admin)):
    """一键回退到指定快照"""
    try:
        return ops.rollback_snapshot(snapshot_name)
    except Exception as e:
        raise HTTPException(400, str(e))

@app.post("/api/ops/backup")
async def backup_db(user = Depends(require_admin)):
    """备份数据库"""
    return ops.backup_database()

@app.get("/api/ops/errors")
async def error_logs(user = Depends(require_admin)):
    """获取错误日志"""
    return ops.get_error_logs()

@app.get("/")
async def index():
    """前端页面"""
    html_path = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# 静态文件
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

