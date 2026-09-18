"""
数据文件管理 —— 管理用户上传的真实数据
上传的文件按 {system}_{entity}.csv 命名，存入 uploaded_data/ 目录
DataConnector优先读上传数据，没有则用mock
"""
import json
from pathlib import Path
import pandas as pd

UPLOAD_DIR = Path(__file__).parent.parent / "uploaded_data"
UPLOAD_DIR.mkdir(exist_ok=True)

# 每张表的字段模板（用于下载模板和校验）
TABLE_SCHEMAS = {
    "ERP_orders": {
        "description": "销售订单",
        "columns": ["order_no", "customer", "product", "qty", "due_date", "status"],
        "example": "SO-001,华为终端,精密壳体A,5000,2026-09-28,在制",
    },
    "ERP_inventory": {
        "description": "库存",
        "columns": ["material", "stock_qty", "unit", "safety_stock"],
        "example": "铝材6061,1200,kg,500",
    },
    "ERP_purchase_orders": {
        "description": "采购订单",
        "columns": ["po_no", "supplier", "material", "qty", "received_qty", "expected_arrival"],
        "example": "PO-001,宝钢金属,铝材6061,2000,800,2026-09-20",
    },
    "ERP_ap_invoices": {
        "description": "应付发票",
        "columns": ["po_no", "receipt_no", "invoice_no", "po_amount", "receipt_amount", "invoice_amount"],
        "example": "PO-001,GR-001,INV-78901,36000,14400,36000",
    },
    "MES_work_orders": {
        "description": "生产工单",
        "columns": ["wo_no", "product", "line", "qty", "completed", "status", "planned_finish"],
        "example": "WO-001,精密壳体A,三号线,5000,1200,生产中,2026-09-25",
    },
    "WMS_stock": {
        "description": "仓库库存(含在途)",
        "columns": ["material", "on_hand", "in_transit", "location"],
        "example": "铝材6061,1200,1200,A-01-03",
    },
    "QMS_inspections": {
        "description": "检验记录",
        "columns": ["batch", "product", "test_item", "result", "value", "standard", "inspector"],
        "example": "B20260915-03,散热片C,平面度,不合格,0.15,≤0.08,张工",
    },
    "QMS_defects": {
        "description": "不良记录",
        "columns": ["batch", "defect_type", "qty", "line", "equipment", "shift", "operator"],
        "example": "B20260915-03,平面度超差,45,二号线,CNC-05,夜班,王师傅",
    },
    "PLM_bom": {
        "description": "BOM清单(产品-组件)",
        "columns": ["product", "component", "qty_per", "unit"],
        "example": "精密壳体A,铝材6061,0.5,kg",
    },
    "SCADA_equipment": {
        "description": "设备台账",
        "columns": ["equip_id", "name", "line", "status", "run_hours", "alarm", "last_maintenance"],
        "example": "CNC-05,加工中心5号,二号线,报警,5800,主轴温度偏高,2026-07-15",
    },
}


def get_table_path(table_key: str) -> Path:
    return UPLOAD_DIR / f"{table_key}.csv"


def has_uploaded(table_key: str) -> bool:
    return get_table_path(table_key).exists()


def load_table(table_key: str) -> list[dict]:
    """读取上传的CSV，返回dict列表；文件不存在返回None"""
    path = get_table_path(table_key)
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, dtype=str).fillna("")
        return df.to_dict("records")
    except Exception as e:
        return None


def save_uploaded(table_key: str, file_bytes: bytes, filename: str) -> tuple[bool, str]:
    """保存上传文件为标准CSV"""
    try:
        # 读取上传文件（支持csv和xlsx）
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(pd.io.common.BytesIO(file_bytes))
        else:
            import io
            df = pd.read_csv(io.BytesIO(file_bytes), dtype=str)
        # 保存为标准CSV
        df.to_csv(get_table_path(table_key), index=False, encoding="utf-8-sig")
        return True, f"成功上传 {table_key}，共{len(df)}行"
    except Exception as e:
        return False, f"上传失败: {str(e)}"


def list_uploaded() -> dict:
    """列出已上传的表"""
    result = {}
    for key in TABLE_SCHEMAS:
        path = get_table_path(key)
        if path.exists():
            try:
                df = pd.read_csv(path)
                result[key] = {"rows": len(df), "cols": list(df.columns)}
            except:
                result[key] = {"rows": "?", "cols": []}
    return result


def download_template(table_key: str) -> bytes:
    """生成CSV模板下载"""
    schema = TABLE_SCHEMAS.get(table_key)
    if not schema:
        return b""
    header = ",".join(schema["columns"])
    csv_content = f"{header}\n{schema['example']}\n"
    return csv_content.encode("utf-8-sig")


def delete_table(table_key: str):
    path = get_table_path(table_key)
    if path.exists():
        path.unlink()
