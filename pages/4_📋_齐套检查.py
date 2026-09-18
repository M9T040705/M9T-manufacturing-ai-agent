"""场景4：生产齐套与欠料预警"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="齐套检查", page_icon="📋", layout="wide")
engine = get_engine()

st.title("📋 生产齐套与欠料预警")
st.caption("基于BOM、库存、在途和排产，提前识别缺料风险")

required = ["PLM_bom", "ERP_inventory", "WMS_stock", "ERP_purchase_orders", "MES_work_orders"]
st.info(check_data_status(required))

q = st.text_input("请描述问题：", value="下周线会不会缺料？")
if st.button("🚀 齐套检查", type="primary"):
    with st.spinner("正在计算BOM需求与库存缺口..."):
        resp = engine.ask(q)
    render_result(resp)

upload_section("齐套检查数据上传", required)
