"""待人工审批页面"""
import streamlit as st
from core.ui_helpers import get_engine

st.set_page_config(page_title="待审批", page_icon="📋", layout="wide")
engine = get_engine()

st.title("📋 待人工审批")
st.caption("高风险动作必须人工拍板 —— Agent可以提建议，但不能替你做决定")

pending = engine.review.pending_list()

if not pending:
    st.success("✅ 暂无待审批事项")
else:
    st.warning(f"🔴 有 **{len(pending)}** 条待审批")
    for r in pending:
        with st.container(border=True):
            st.markdown(f"### ⚠ {r.action}")
            st.caption(f"申请编号：{r.request_id}")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("风险等级", r.risk_level.value)
            with c2:
                st.metric("审批人", r.approver_role)
            with c3:
                st.metric("当前状态", r.status.value)
            if r.context:
                with st.expander("查看上下文"):
                    st.json(r.context)
            cA, cB = st.columns(2)
            with cA:
                if st.button(f"✅ 批准", key=f"app_{r.request_id}", type="primary"):
                    engine.review.approve(r.request_id, "当前用户")
                    st.success("已批准")
                    st.rerun()
            with cB:
                if st.button(f"❌ 驳回", key=f"rej_{r.request_id}"):
                    engine.review.reject(r.request_id, "当前用户")
                    st.info("已驳回")
                    st.rerun()
