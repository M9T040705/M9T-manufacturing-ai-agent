"""场景3：管理每日一页"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="管理日报", page_icon="📊", layout="wide")
engine = get_engine()

st.title("📊 管理每日一页")
st.caption("让管理更聚焦，看清今天该盯什么")

required = ["MES_work_orders", "QMS_defects", "SCADA_equipment", "ERP_inventory"]
st.info(check_data_status(required))

q = st.text_input("请描述问题：", value="今天工厂我该盯什么？")
if st.button("🚀 生成日报", type="primary"):
    with st.spinner("正在汇总全厂异常..."):
        resp = engine.ask(q)
    render_result(resp)

upload_section("管理日报数据上传", required)
