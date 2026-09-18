"""
制造业AI Agent 平台 —— 主页/导航
"""
import streamlit as st
from core.ui_helpers import get_engine, check_data_status
from core import data_store

st.set_page_config(page_title="制造业AI Agent平台", page_icon="🏭", layout="wide")

engine = get_engine()

st.title("🏭 制造业AI Agent平台")
st.caption("懂公司 · 能办事 · 管得住 · 持续变强")

# 数据状态
uploaded = data_store.list_uploaded()
st.info(f"📊 当前已上传 **{len(uploaded)}** 张数据表 | 未上传的自动使用示例数据")

# 6个场景卡片
st.subheader("🎯 六大业务场景")

scenes = [
    ("1_💰_采购对账", "💰", "采购三单匹配对账", "自动核对采购单/收货单/发票，减少扯皮", "项目一·降本增效"),
    ("2_📦_交期答复", "📦", "销售交期答复", "自动拉订单+库存+在制，5分钟给出交期", "项目一·降本增效"),
    ("3_📊_管理日报", "📊", "管理每日一页", "汇总全厂异常，按优先级排序", "项目一·降本增效"),
    ("4_📋_齐套检查", "📋", "生产齐套欠料", "BOM+库存+在途，提前发现缺料风险", "项目二·智能生产"),
    ("5_🔧_设备维保", "🔧", "设备点检维保", "报警汇总+维修经验，减少非计划停机", "项目四·设备专项"),
    ("6_🔍_质量追溯", "🔍", "质量批次追溯", "批次全链路追溯+根因分析", "项目五·质量专项"),
]

cols = st.columns(3)
for idx, (page_name, icon, title, desc, project) in enumerate(scenes):
    with cols[idx % 3]:
        with st.container(border=True):
            st.markdown(f"### {icon} {title}")
            st.caption(desc)
            st.caption(f"📌 {project}")
            if st.button(f"进入 →", key=f"nav_{idx}", use_container_width=True):
                st.switch_page(f"pages/{page_name}.py")

st.divider()

# 其他功能
st.subheader("🛠 平台功能")
c1, c2, c3 = st.columns(3)
with c1:
    if st.button("📁 数据上传", use_container_width=True):
        st.switch_page("pages/9_📁_数据上传.py")
with c2:
    if st.button("📋 待审批", use_container_width=True):
        st.switch_page("pages/7_📋_待审批.py")
with c3:
    if st.button("📝 审计日志", use_container_width=True):
        st.switch_page("pages/8_📝_审计日志.py")

st.divider()
st.caption("💡 高风险动作（付款/交期/停线/召回）必须人工审批 | 所有操作留痕可审计")
