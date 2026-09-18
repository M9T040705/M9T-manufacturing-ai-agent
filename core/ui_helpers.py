"""
共享UI组件 —— 各场景页面复用
"""
import streamlit as st

from core.agent_engine import AgentEngine
from core.data_connector import DataConnector
from core.knowledge_base import KnowledgeBase
from core.human_review import HumanReviewGate
from core import data_store
from skills import register_all_skills


@st.cache_resource
def get_engine():
    """全局唯一的Agent引擎实例（多页面共享）"""
    connector = DataConnector(mode="auto")
    kb = KnowledgeBase()
    gate = HumanReviewGate()
    engine = AgentEngine(connector=connector, kb=kb, review_gate=gate)
    register_all_skills(engine)
    return engine


def render_result(resp):
    """渲染Agent回答结果"""
    st.subheader("📤 Agent 回答")
    st.markdown(resp.answer)

    col1, col2 = st.columns([2, 1])
    with col1:
        with st.expander("⚙️ 处理过程"):
            st.caption(f"意图识别：**{resp.intent}**")
            for i, step in enumerate(resp.steps_taken, 1):
                st.text(f"{i}. {step}")
    with col2:
        if resp.data_summary:
            st.caption("📊 数据摘要：")
            for k, v in resp.data_summary.items():
                st.text(f"  {k}: {v}")

    if resp.need_human_review and resp.review_request:
        st.warning(
            f"🔴 **需人工审批**：{resp.review_request['action']}\n\n"
            f"审批人：{resp.review_request['approver']} | "
            f"风险等级：{resp.review_request['risk_level']}\n\n"
            f"请到「待审批」页面处理。"
        )


def upload_section(title: str, tables: list[str]):
    """在页面内渲染数据上传折叠区
    tables: 需要上传的表key列表，如 ["ERP_purchase_orders", "ERP_ap_invoices"]
    """
    with st.expander(f"📁 {title}（上传真实数据替换示例）"):
        st.caption("先下载模板，按模板填好数据后上传。支持CSV/Excel。")
        for t in tables:
            schema = data_store.TABLE_SCHEMAS.get(t, {})
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**{t}** — {schema.get('description', '')}")
                    st.caption(f"字段：{', '.join(schema.get('columns', []))}")
                    uploaded = data_store.has_uploaded(t)
                    if uploaded:
                        info = data_store.list_uploaded().get(t, {})
                        st.success(f"✅ 已上传（{info.get('rows', '?')}行）")
                with c2:
                    st.download_button(
                        "⬇ 模板",
                        data=data_store.download_template(t),
                        file_name=f"{t}_template.csv",
                        mime="text/csv",
                        key=f"dl_{t}",
                    )
                    up = st.file_uploader(
                        "上传",
                        type=["csv", "xlsx", "xls"],
                        key=f"up_{t}",
                        label_visibility="collapsed",
                    )
                    if up:
                        success, msg = data_store.save_uploaded(t, up.read(), up.name)
                        if success:
                            st.success(msg)
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error(msg)


def check_data_status(required_tables: list[str]) -> str:
    """检查当前场景依赖的数据表是否已上传，返回状态提示"""
    uploaded = data_store.list_uploaded()
    missing = [t for t in required_tables if t not in uploaded]
    if not missing:
        return "✅ 使用已上传的真实数据"
    else:
        return f"⚠ 使用示例数据。上传以下表格后自动切换真实数据：{', '.join(missing)}"
