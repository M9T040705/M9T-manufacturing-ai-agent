"""数据上传管理页面 —— 统一管理所有数据表"""
import streamlit as st
from core import data_store

st.set_page_config(page_title="数据上传", page_icon="📁", layout="wide")

st.title("📁 数据上传中心")
st.caption("上传你的真实生产数据（CSV/Excel），Agent自动使用真实数据代替示例数据")

uploaded = data_store.list_uploaded()

# 按系统分组
groups = {
    "ERP（订单/库存/采购/应付）": ["ERP_orders", "ERP_inventory", "ERP_purchase_orders", "ERP_ap_invoices"],
    "MES（工单/生产进度）": ["MES_work_orders"],
    "WMS（仓库/批次）": ["WMS_stock"],
    "QMS（检验/质量）": ["QMS_inspections", "QMS_defects"],
    "PLM（BOM/工艺）": ["PLM_bom"],
    "SCADA（设备）": ["SCADA_equipment"],
}

for group_name, tables in groups.items():
    st.subheader(group_name)
    for t in tables:
        schema = data_store.TABLE_SCHEMAS.get(t, {})
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.write(f"**{t}** — {schema.get('description', '')}")
                st.caption(f"字段：{', '.join(schema.get('columns', []))}")
                if t in uploaded:
                    st.success(f"✅ 已上传（{uploaded[t].get('rows','?')}行）")
                else:
                    st.warning("⚠ 未上传，使用示例数据")
            with c2:
                st.download_button(
                    "⬇ 下载模板",
                    data=data_store.download_template(t),
                    file_name=f"{t}_template.csv",
                    mime="text/csv",
                    key=f"dl_all_{t}",
                )
            with c3:
                up = st.file_uploader(
                    "上传文件",
                    type=["csv", "xlsx", "xls"],
                    key=f"up_all_{t}",
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

st.divider()
st.info(
    "💡 **上传说明：**\n"
    "1. 先下载模板，按模板列名整理你的数据\n"
    "2. 支持CSV和Excel(.xlsx)格式\n"
    "3. 上传后该表立即生效，Agent自动切换到真实数据\n"
    "4. 如需删除，直接删除 uploaded_data/ 目录下对应文件\n"
    "5. 未上传的表继续使用示例数据，不影响其他场景使用"
)
