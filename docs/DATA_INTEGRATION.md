# 数据接入指南

> 本系统设计为**数据无关**：出厂自带示例数据，所有场景可直接演示。
> 部署到真实企业后，按本文档接入真实数据即可自动切换，**不用改任何代码**。

---

## 一、数据架构

```
Agent业务逻辑（6个场景技能）
       ↓ 统一调用
DataConnector（数据适配层）
       ↓ 自动判断
  ┌────┴────┐
  │         │
上传CSV   示例mock
(真实数据)  (兜底)
```

**优先级：** 上传的真实数据 > 内置示例数据。只要传了对应表，自动用真实的；没传就用示例数据演示。

---

## 二、六大数据域

| 系统 | 用途 | 对应场景 | 必须接吗 |
|------|------|---------|---------|
| **ERP** | 订单/库存/采购/应付 | 对账、交期、齐套 | 优先接 |
| **MES** | 工单/报工/生产进度 | 日报、齐套 | 次优先 |
| **WMS** | 出入库/批次 | 齐套、追溯 | 看需求 |
| **QMS** | 检验/不良记录 | 质量追溯 | 做追溯才需要 |
| **PLM** | BOM/工艺路线 | 齐套、追溯 | 做齐套必须接 |
| **SCADA** | 设备状态/报警 | 设备维保 | 做设备才需要 |

---

## 三、接入方式（三种，从易到难）

### 方式1：CSV/Excel 上传（最简单，推荐先用）

1. 登录管理员账号
2. 左侧「📁 数据接入」
3. 点「下载模板」拿到CSV格式
4. 把企业数据按模板填好
5. 点「上传」
6. 完成——系统自动用真实数据，不用重启

**适合：** 初期演示、小规模试点、企业能导出Excel的场景

### 方式2：数据库直连（企业有ERP/MES的情况）

在 `core/data_connector.py` 里加一个新方法：

```python
def query_erp(self, entity: str, **kwargs):
    # 原来是：return self._load(...)
    # 改成：先查企业真实数据库，查不到再用上传/mock
    real = self._query_erp_db(entity)  # 写个查库函数
    if real: return real
    return self._load(f"ERP_{entity}", lambda: self._mock_erp(entity, **kwargs))
```

**适合：** 企业有SQL Server / MySQL / Oracle，能开放只读账号

### 方式3：设备实时数据（SCADA/OPC UA）

车间装一个轻量采集器（Python脚本）：
- 每分钟读一次PLC/CNC数据
- 存成CSV到 `uploaded_data/SCADA_equipment.csv`
- 系统自动识别为真实数据

**适合：** 做设备维保、OEE、预测性维护时

---

## 四、各表字段要求

### ERP_orders（订单）
| 字段 | 说明 |
|------|------|
| order_no | 订单号 |
| customer | 客户名称 |
| product | 产品名称 |
| qty | 数量 |
| due_date | 交期（YYYY-MM-DD） |
| status | 状态 |

### ERP_inventory（库存）
| 字段 | 说明 |
|------|------|
| material | 物料名称 |
| stock_qty | 现有库存 |
| unit | 单位 |
| safety_stock | 安全库存 |

### ERP_ap_invoices（应付/发票）
| 字段 | 说明 |
|------|------|
| po_no | 采购单号 |
| receipt_no | 收货单号 |
| invoice_no | 发票号 |
| po_amount | 采购金额 |
| receipt_amount | 收货金额 |
| invoice_amount | 发票金额 |

### MES_work_orders（工单）
| 字段 | 说明 |
|------|------|
| wo_no | 工单号 |
| product | 产品 |
| line | 产线 |
| qty | 计划数量 |
| completed | 已完成数量 |
| status | 状态 |
| planned_finish | 计划完工日期 |

### PLM_bom（物料清单）
| 字段 | 说明 |
|------|------|
| product | 产品名称 |
| component | 子件/原材料 |
| qty_per | 单位用量 |
| unit | 单位 |

### SCADA_equipment（设备状态）
| 字段 | 说明 |
|------|------|
| equip_id | 设备编号 |
| name | 设备名称 |
| line | 所属产线 |
| status | 运行状态 |
| run_hours | 运行时长 |
| alarm | 报警信息（分号分隔多个） |
| last_maintenance | 上次保养日期 |

---

## 五、怎么知道接没接上

管理员登录后 → 「📁 数据接入」页面：
- ✅ 绿色 = 已接真实数据
- ⚠️ 黄色 = 部分接入
- ⏳ 灰色 = 还是示例数据

**不影响使用：** 没接的数据系统用示例数据跑着，业务人员照样用，不会报错。
