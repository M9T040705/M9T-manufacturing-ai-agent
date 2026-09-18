"""场景6：质量批次追溯与归因"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="质量追溯", page_icon="🔍", layout="wide")
engine = get_engine()

st.title("🔍 质量批次追溯与归因")
st.caption("打通批次、工艺、检验和设备数据，快速定位问题批次")

required = ["QMS_inspections", "QMS_defects", "WMS_stock"]
st.info(check_data_status(required))

q = st.text_input("请描述问题：", value="这批客诉是哪一段出的？")
if st.button("🚀 开始追溯", type="primary"):
    with st.spinner("正在拉通批次全链路数据..."):
        resp = engine.ask(q)
    render_result(resp)

upload_section("质量数据上传", required)
