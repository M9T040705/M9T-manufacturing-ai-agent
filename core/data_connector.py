"""
数据连接层 —— 对应图3第1个能力"跨系统取数"和图5"常见要接的系统"
优先读取用户上传的真实数据（CSV/Excel），没有则用模拟数据。
真实接入：①在"数据上传"页传Excel 或 ②替换为真实API调用。
"""
from datetime import datetime, timedelta
from typing import Any

from . import data_store


class DataConnector:
    """
    统一数据入口。Agent通过本类取数，不直接碰底层系统。
    取数优先级：上传文件 > mock模拟数据
    """

    def __init__(self, mode: str = "auto"):
        self.mode = mode

    def _load(self, table_key: str, mock_fn):
        """统一取数：先查上传，没有用mock"""
        if self.mode in ("auto", "upload"):
            uploaded = data_store.load_table(table_key)
            if uploaded is not None:
                return uploaded
        return mock_fn()

    # ── ERP：订单/库存/采购/应付 ──────────────────────────
    def query_erp(self, entity: str, **kwargs):
        return self._load(f"ERP_{entity}", lambda: self._mock_erp(entity, **kwargs))

    # ── MES：工单/报工/生产进度 ─────────────────────────
    def query_mes(self, entity: str, **kwargs):
        return self._load(f"MES_{entity}", lambda: self._mock_mes(entity, **kwargs))

    # ── WMS：出入库/库位/批次 ───────────────────────────
    def query_wms(self, entity: str, **kwargs):
        return self._load(f"WMS_{entity}", lambda: self._mock_wms(entity, **kwargs))

    # ── QMS：检验/不良/质量追溯 ──────────────────────────
    def query_qms(self, entity: str, **kwargs):
        return self._load(f"QMS_{entity}", lambda: self._mock_qms(entity, **kwargs))

    # ── PLM：BOM/图纸/工艺 ───────────────────────────────
    def query_plm(self, entity: str, **kwargs):
        if entity == "bom":
            uploaded = data_store.load_table("PLM_bom")
            if uploaded is not None:
                bom_map = {}
                for row in uploaded:
                    prod = row.get("product", "")
                    bom_map.setdefault(prod, []).append({
                        "material": row.get("component", ""),
                        "qty_per": float(row.get("qty_per", 0) or 0),
                        "unit": row.get("unit", ""),
                    })
                return [{"product": k, "components": v} for k, v in bom_map.items()]
        return self._load(f"PLM_{entity}", lambda: self._mock_plm(entity, **kwargs))

    # ── SCADA：设备状态/运行数据 ────────────────────────
    def query_scada(self, entity: str, **kwargs):
        uploaded = data_store.load_table(f"SCADA_{entity}")
        if uploaded is not None:
            for row in uploaded:
                alarm_str = row.get("alarm", "")
                if isinstance(alarm_str, str) and alarm_str:
                    row["alarm"] = [a.strip() for a in str(alarm_str).split(";") if a.strip()]
                else:
                    row["alarm"] = []
                try:
                    row["run_hours"] = float(row.get("run_hours", 0) or 0)
                except:
                    row["run_hours"] = 0
            return uploaded
        return self._load(f"SCADA_{entity}", lambda: self._mock_scada(entity, **kwargs))

    # ════════════════════ 模拟数据 ════════════════════
    # 以下数据为示例工厂场景，真实部署时替换为真实系统数据

    def _mock_erp(self, entity: str, **kwargs) -> list[dict]:
        now = datetime.now()
        data = {
            "orders": [
                {"order_no": "SO-20260918-001", "customer": "华为终端", "product": "精密壳体A",
                 "qty": 5000, "due_date": (now + timedelta(days=10)).strftime("%Y-%m-%d"), "status": "在制"},
                {"order_no": "SO-20260918-002", "customer": "比亚迪", "product": "连接件B",
                 "qty": 12000, "due_date": (now + timedelta(days=7)).strftime("%Y-%m-%d"), "status": "待投产"},
                {"order_no": "SO-20260915-003", "customer": "宁德时代", "product": "散热片C",
                 "qty": 8000, "due_date": (now + timedelta(days=3)).strftime("%Y-%m-%d"), "status": "在制"},
            ],
            "inventory": [
                {"material": "铝材6061", "stock_qty": 1200, "unit": "kg", "safety_stock": 500},
                {"material": "不锈钢304", "stock_qty": 800, "unit": "kg", "safety_stock": 300},
                {"material": "M6螺丝", "stock_qty": 50000, "unit": "个", "safety_stock": 20000},
                {"material": "密封圈", "stock_qty": 3000, "unit": "个", "safety_stock": 10000},
            ],
            "purchase_orders": [
                {"po_no": "PO-20260910-01", "supplier": "宝钢金属", "material": "铝材6061",
                 "qty": 2000, "received_qty": 800, "expected_arrival": (now + timedelta(days=2)).strftime("%Y-%m-%d")},
                {"po_no": "PO-20260908-03", "supplier": "昆山密封件厂", "material": "密封圈",
                 "qty": 20000, "received_qty": 5000, "expected_arrival": (now + timedelta(days=5)).strftime("%Y-%m-%d")},
            ],
            "ap_invoices": [
                {"po_no": "PO-20260910-01", "receipt_no": "GR-0912-01", "invoice_no": "INV-78901",
                 "po_amount": 36000, "receipt_amount": 14400, "invoice_amount": 36000},
                {"po_no": "PO-20260908-03", "receipt_no": "GR-0910-05", "invoice_no": "INV-78899",
                 "po_amount": 20000, "receipt_amount": 5000, "invoice_amount": 5000},
            ],
        }
        return data.get(entity, [])

    def _mock_mes(self, entity: str, **kwargs) -> list[dict]:
        data = {
            "work_orders": [
                {"wo_no": "WO-20260918-101", "product": "精密壳体A", "line": "三号线",
                 "qty": 5000, "completed": 1200, "status": "生产中", "planned_finish": "2026-09-25"},
                {"wo_no": "WO-20260918-102", "product": "连接件B", "line": "一号线",
                 "qty": 12000, "completed": 0, "status": "待投产", "planned_finish": "2026-09-27"},
                {"wo_no": "WO-20260915-103", "product": "散热片C", "line": "二号线",
                 "qty": 8000, "completed": 6500, "status": "生产中", "planned_finish": "2026-09-20"},
            ],
            "shift_records": [
                {"date": "2026-09-18", "line": "三号线", "shift": "白班", "output": 400, "defect_qty": 12},
                {"date": "2026-09-18", "line": "二号线", "shift": "夜班", "output": 350, "defect_qty": 8},
            ],
        }
        return data.get(entity, [])

    def _mock_wms(self, entity: str, **kwargs) -> list[dict]:
        data = {
            "stock": [
                {"material": "铝材6061", "on_hand": 1200, "in_transit": 1200, "location": "A-01-03"},
                {"material": "密封圈", "on_hand": 3000, "in_transit": 15000, "location": "B-02-01"},
            ],
            "in_out": [
                {"date": "2026-09-17", "material": "铝材6061", "type": "入库", "qty": 800, "batch": "B20260917-01"},
                {"date": "2026-09-18", "material": "密封圈", "type": "出库", "qty": 2000, "batch": "B20260915-03"},
            ],
        }
        return data.get(entity, [])

    def _mock_qms(self, entity: str, **kwargs) -> list[dict]:
        data = {
            "inspections": [
                {"batch": "B20260915-03", "product": "散热片C", "test_item": "平面度",
                 "result": "不合格", "value": 0.15, "standard": "≤0.08", "inspector": "张工"},
                {"batch": "B20260917-01", "product": "精密壳体A", "test_item": "粗糙度",
                 "result": "合格", "value": 1.6, "standard": "≤3.2", "inspector": "李工"},
            ],
            "defects": [
                {"batch": "B20260915-03", "defect_type": "平面度超差", "qty": 45,
                 "line": "二号线", "equipment": "CNC-05", "shift": "夜班", "operator": "王师傅"},
            ],
        }
        return data.get(entity, [])

    def _mock_plm(self, entity: str, **kwargs) -> list[dict]:
        data = {
            "bom": [
                {"product": "精密壳体A", "components": [
                    {"material": "铝材6061", "qty_per": 0.5, "unit": "kg"},
                    {"material": "M6螺丝", "qty_per": 4, "unit": "个"},
                ]},
                {"product": "连接件B", "components": [
                    {"material": "不锈钢304", "qty_per": 0.2, "unit": "kg"},
                    {"material": "密封圈", "qty_per": 2, "unit": "个"},
                ]},
                {"product": "散热片C", "components": [
                    {"material": "铝材6061", "qty_per": 0.3, "unit": "kg"},
                ]},
            ],
            "routing": [
                {"product": "精密壳体A", "steps": ["下料", "CNC加工", "阳极氧化", "检验", "包装"]},
                {"product": "散热片C", "steps": ["下料", "CNC加工", "清洗", "检验", "包装"]},
            ],
        }
        return data.get(entity, [])

    def _mock_scada(self, entity: str, **kwargs) -> list[dict]:
        data = {
            "equipment": [
                {"equip_id": "CNC-01", "name": "加工中心1号", "line": "一号线",
                 "status": "运行", "run_hours": 4200, "alarm": [], "last_maintenance": "2026-08-20"},
                {"equip_id": "CNC-05", "name": "加工中心5号", "line": "二号线",
                 "status": "报警", "run_hours": 5800,
                 "alarm": ["主轴温度偏高", "润滑油位低"], "last_maintenance": "2026-07-15"},
                {"equip_id": "INJ-03", "name": "注塑机3号", "line": "三号线",
                 "status": "运行", "run_hours": 3100, "alarm": [], "last_maintenance": "2026-09-01"},
            ],
            "alarms": [
                {"equip_id": "CNC-05", "time": "2026-09-18 14:22", "alarm": "主轴温度偏高", "duration_min": 15},
                {"equip_id": "CNC-05", "time": "2026-09-18 09:10", "alarm": "润滑油位低", "duration_min": 5},
            ],
        }
        return data.get(entity, [])
