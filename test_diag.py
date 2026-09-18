"""测试智能诊断"""
import requests

tests = [
    "财务每个月对账要花5天，经常出错",
    "客户老催交期，销售要问好几个人才能答复",
    "设备老停机，维修全靠老师傅经验",
    "客户投诉质量问题，追溯批次要找好几天",
]
for t in tests:
    r = requests.post("http://localhost:8502/api/diagnose", json={"description": t})
    d = r.json()
    rec = d.get("recommendation")
    print(f"问题: {t}")
    if rec:
        print(f"  -> 推荐: {rec['title']}")
        print(f"  -> 理由: {rec['reason']}")
    else:
        print(f"  -> {d['message']}")
    print()
