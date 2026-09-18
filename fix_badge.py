"""修复审批完角标不消失"""
path = r"E:\fde\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = """async function doApprove(id) { await api(`/api/approve/${id}?approver=当前用户`, {method:"POST"}); bindApprovalEvents(); }
async function doReject(id) { await api(`/api/reject/${id}?approver=当前用户`, {method:"POST"}); bindApprovalEvents(); }"""

new = """async function doApprove(id) { await api(`/api/approve/${id}?approver=当前用户`, {method:"POST"}); bindApprovalEvents(); updateApprovalBadge(); }
async function doReject(id) { await api(`/api/reject/${id}?approver=当前用户`, {method:"POST"}); bindApprovalEvents(); updateApprovalBadge(); }"""

content = content.replace(old, new)
with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
