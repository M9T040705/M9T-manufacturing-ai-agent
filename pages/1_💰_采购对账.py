"""场景1：采购三单匹配对账"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="采购对账", page_icon="💰", layout="wide")
engine = get_engine()

st.title("💰 采购三单匹配与对账")
st.caption("让对账更快更准，减少扯皮")

# 数据状态
required = ["ERP_purchase_orders", "ERP_ap_invoices", "ERP_inventory"]
st.info(check_data_status(required))

# 问题输入
q = st.text_input("请描述问题：", value="这个月对账有没有异常？")
if st.button("🚀 开始分析", type="primary"):
    with st.spinner("正在跨系统取数、核对..."):
        resp = engine.ask(q)
    render_result(resp)

# 数据上传
upload_section("采购对账数据上传", required)
