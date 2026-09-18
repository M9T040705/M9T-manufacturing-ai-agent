"""
数据治理层 —— FDE第二层能力
1. 数据质量校验（缺字段/格式不对自动提醒）
2. 数据字典统一（不同系统字段名自动映射）
3. 数据血缘追踪（知道数据从哪个系统来的）
"""
from datetime import datetime
from typing import Optional


# ── 数据字典：不同系统的字段名映射 ──────────────────
# 同一个业务概念，不同系统叫不同名字，统一映射成标准字段名
FIELD_MAPPING = {
    # 物料相关
    "物料编码": "material_code",
    "料号": "material_code",
    "物料号": "material_code",
    "item_code": "material_code",
    "product_code": "material_code",
    # 物料名称
    "物料名称": "material_name",
    "品名": "material_name",
    "item_name": "material_name",
    "product_name": "material_name",
    # 数量
    "数量": "qty",
    "qty": "qty",
    "quantity": "qty",
    "num": "qty",
    # 单价
    "单价": "unit_price",
    "price": "unit_price",
    "unit_price": "unit_price",
    # 仓库
    "仓库": "warehouse",
    "warehouse": "warehouse",
    "库位": "location",
    "location": "location",
    # 订单号
    "订单号": "order_no",
    "order_no": "order_no",
    "order_number": "order_no",
    "po_no": "order_no",
    # 供应商
    "供应商": "supplier",
    "supplier": "supplier",
    "vendor": "supplier",
    # 设备
    "设备编号": "equip_id",
    "设备号": "equip_id",
    "equip_id": "equip_id",
    "machine_id": "equip_id",
    "设备名称": "equip_name",
    "machine_name": "equip_name",
    # 批次
    "批次号": "batch_no",
    "批次": "batch_no",
    "batch_no": "batch_no",
    "batch": "batch_no",
    # 日期
    "日期": "date",
    "date": "date",
    "创建日期": "created_at",
    "create_date": "created_at",
    "交货日期": "delivery_date",
    "due_date": "delivery_date",
}


class DataGovernance:
    """数据治理：质量校验 + 字典映射 + 血缘追踪"""

    def __init__(self):
        self.issues: list[dict] = []  # 数据质量问题
        self.lineage: list[dict] = []  # 数据血缘记录

    def normalize_fields(self, rows: list[dict], source: str) -> list[dict]:
        """
        数据字典统一：把不同系统的字段名映射成标准字段名
        同时记录数据血缘
        """
        if not rows:
            return rows

        normalized = []
        for row in rows:
            new_row = {}
            for k, v in row.items():
                std_key = FIELD_MAPPING.get(k.strip(), k.strip())
                new_row[std_key] = v
            normalized.append(new_row)

            # 记录血缘（第一条记录就行，不用每条都记）
            break
        else:
            normalized = []

        # 重新处理所有行
        normalized = []
        for row in rows:
            new_row = {}
            for k, v in row.items():
                std_key = FIELD_MAPPING.get(k.strip(), k.strip())
                new_row[std_key] = v
            normalized.append(new_row)

        # 记录血缘
        if rows:
            self.lineage.append({
                "source": source,
                "rows": len(rows),
                "fields": list(rows[0].keys()) if rows else [],
                "normalized_fields": list(normalized[0].keys()) if normalized else [],
                "time": datetime.now().isoformat(),
            })

        return normalized

    def validate_data(self, rows: list[dict], table_name: str, required_fields: list[str] = None) -> list[dict]:
        """
        数据质量校验：检查必填字段、数据量、格式
        返回问题列表
        """
        issues = []

        # 1. 数据量检查
        if not rows:
            issues.append({
                "table": table_name,
                "type": "empty",
                "severity": "high",
                "message": f"{table_name} 表为空，没有数据",
            })
            return issues

        # 2. 必填字段检查
        if required_fields:
            for field in required_fields:
                missing_count = sum(1 for r in rows if not r.get(field))
                if missing_count > 0:
                    issues.append({
                        "table": table_name,
                        "type": "missing_field",
                        "severity": "medium",
                        "field": field,
                        "message": f"{table_name}.{field} 有 {missing_count}/{len(rows)} 行缺失",
                    })

        # 3. 空值检查（关键字段）
        if rows:
            for field in rows[0].keys():
                empty_count = sum(1 for r in rows if r.get(field) in (None, "", []))
                if empty_count == len(rows):
                    issues.append({
                        "table": table_name,
                        "type": "all_empty",
                        "severity": "low",
                        "field": field,
                        "message": f"{table_name}.{field} 全部为空",
                    })

        self.issues.extend(issues)
        return issues

    def get_quality_report(self) -> dict:
        """获取数据质量报告"""
        high = sum(1 for i in self.issues if i["severity"] == "high")
        medium = sum(1 for i in self.issues if i["severity"] == "medium")
        low = sum(1 for i in self.issues if i["severity"] == "low")
        return {
            "total_issues": len(self.issues),
            "high": high,
            "medium": medium,
            "low": low,
            "issues": self.issues,
            "lineage": self.lineage,
        }

    def clear(self):
        """清空（每次启动时调用）"""
        self.issues = []
        self.lineage = []
