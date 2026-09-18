"""审计日志查看页面"""
import streamlit as st
from pathlib import Path
import json

st.set_page_config(page_title="审计日志", page_icon="📝", layout="wide")

AUDIT_DIR = Path(__file__).parent.parent / "audit"

st.title("📝 审计日志")
st.caption("所有Agent取数、分析、建议、动作全链路留痕，可回放可审计")

files = sorted(AUDIT_DIR.glob("audit_*.json"), reverse=True)
if not files:
    st.info("暂无审计记录")
else:
    st.caption(f"共 {len(files)} 条审计记录")
    for f in files[:20]:
        with st.expander(f"📄 {f.name}"):
            try:
                with open(f, encoding="utf-8") as fp:
                    entries = json.load(fp)
                for e in entries:
                    st.text(f"[{e.get('timestamp','')}] {e.get('stage','')}: {e.get('action','')}")
            except Exception as ex:
                st.error(f"读取失败: {ex}")
