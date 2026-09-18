"""场景5：设备点检维保"""
import streamlit as st
from core.ui_helpers import get_engine, render_result, upload_section, check_data_status

st.set_page_config(page_title="设备维保", page_icon="🔧", layout="wide")
engine = get_engine()

st.title("🔧 设备点检与维保建议")
st.caption("结合设备运行数据、报警记录和维修经验，识别异常风险")

required = ["SCADA_equipment"]
st.info(check_data_status(required))

q = st.text_input("请描述问题：", value="今天设备要盯什么？")
if st.button("🚀 设备巡检", type="primary"):
    with st.spinner("正在读取设备状态和报警..."):
        resp = engine.ask(q)
    render_result(resp)

upload_section("设备数据上传", required)
