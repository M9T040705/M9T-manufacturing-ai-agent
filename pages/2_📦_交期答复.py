"""场景2：销售交期答复"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="交期答复", page_icon="📦", layout="wide")
engine = get_engine()

st.title("📦 销售交期答复")
st.caption("让交期答复更快更稳，减少来回确认")

required = ["ERP_orders", "ERP_inventory", "MES_work_orders", "PLM_bom"]
st.info(check_data_status(required))

q = st.text_input("请描述问题：", value="这单什么时候能出？")
if st.button("🚀 开始分析", type="primary"):
    with st.spinner("正在拉订单、库存、在制、排产..."):
        resp = engine.ask(q)
    render_result(resp)

upload_section("交期答复数据上传", required)
