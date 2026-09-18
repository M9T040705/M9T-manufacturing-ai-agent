"""改测试脚本路径"""
path = r"E:\FDE项目\fde_test\run_tests.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(r"E:\fde_test\test_report.json", r"E:\FDE项目\fde_test\test_report.json")
content = content.replace(r"E:\fde_test", r"E:\FDE项目\fde_test")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
print("done")
