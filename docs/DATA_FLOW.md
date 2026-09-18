# 系统数据流动图

---

## 一、完整总览图（一张大图）

```mermaid
flowchart TB
    subgraph 数据源层
        ERP[🏢 ERP系统<br/>订单/库存/采购/应付]
        MES[🏭 MES系统<br/>工单/报工]
        WMS[📦 WMS系统<br/>出入库/批次]
        QMS[🔍 QMS系统<br/>检验/不良]
        PLM[📋 PLM系统<br/>BOM/工艺]
        SCADA[⚙️ SCADA设备层<br/>设备状态/报警]
    end

    subgraph 数据接入层
        DC[DataConnector 数据适配层<br/>上传CSV优先 + mock兜底<br/>统一6大系统取数接口]
    end

    subgraph 智能引擎核心
        direction TB
        IE[Agent引擎<br/>意图识别 → 路由 → 取数 → 分析]
        KB[知识库Vault<br/>规则/经验 markdown]
        HR[人审闸门<br/>高风险动作审批]
        SS[安全扫描<br/>出站脱敏]
    end

    subgraph 状态与存储
        DB[(SQLite 状态层<br/>对话历史/用户/反馈/案例)]
    end

    subgraph 用户层
        FIN[💰 财务部]
        SAL[📦 销售部]
        PRO[🏗️ 生产部]
        QC[🔍 质量部]
        BOSS[👔 厂长]
        ADMIN[⚙️ 管理员]
    end

    ERP --> DC
    MES --> DC
    WMS --> DC
    QMS --> DC
    PLM --> DC
    SCADA --> DC

    DC --> IE
    KB --> IE
    IE --> HR --> SS
    SS --> DB

    IE --> FIN
    IE --> SAL
    IE --> PRO
    IE --> QC
    IE --> BOSS
    IE --> ADMIN

    DB --> IE
```

**一句话说清楚：** 6个业务系统的数据 → 经过适配层统一格式 → Agent引擎按规则分析（规则从知识库读）→ 高风险过人审 → 安全扫描 → 存SQLite → 6个部门按权限看自己的结果。

---

## 二、各部门数据流动图

### 财务部 —— 采购三单匹配对账

```mermaid
flowchart LR
    subgraph 数据来源
        ERP_PO[ERP 采购单<br/>purchase_orders]
        ERP_GR[ERP 收货记录<br/>receipts]
        ERP_INV[ERP 发票应付<br/>ap_invoices]
    end

    subgraph 系统处理
        DC[数据适配层]
        MATCH[三单匹配引擎<br/>核对数量/金额/到货]
        DIFF[差异识别<br/>多开/少开/未到货]
    end

    subgraph 财务部看到的
        REPORT[📋 对账异常清单<br/>🔴 差异标红]
        APPROVE[✅ 付款审批<br/>过人审闸门]
    end

    ERP_PO --> DC
    ERP_GR --> DC
    ERP_INV --> DC
    DC --> MATCH --> DIFF
    DIFF --> REPORT
    REPORT --> APPROVE

    APPROVE -.->|审批结果记录| DB[(审计日志)]
```

**财务部用户看到的：** 本月对账异常清单——哪些发票和收货对不上、哪些货还没到。不用翻Excel三单核对了。

---

### 销售部 —— 交期答复

```mermaid
flowchart LR
    subgraph 数据来源
        ERP_ORDER[ERP 销售订单<br/>orders]
        ERP_STOCK[ERP 库存<br/>inventory]
        MES_WO[MES 在制工单<br/>work_orders]
    end

    subgraph 系统处理
        DC[数据适配层]
        CHECK[库存够不够?]
        CALC[算交期<br/>现有库存 + 在制完成时间]
        RISK[风险提示<br/>物料短缺/设备报警]
    end

    subgraph 销售部看到的
        ANSWER[📦 建议交期<br/>+ 风险提示]
    end

    ERP_ORDER --> DC
    ERP_STOCK --> DC
    MES_WO --> DC
    DC --> CHECK --> CALC --> RISK
    RISK --> ANSWER

    RISK -.->|缺料预警| PRO[🏗️ 生产部]
```

**销售部用户看到的：** 客户问"这单什么时候能出？"，输入产品数量，5秒给出建议交期+风险提示。不用打电话问车间了。

**跨部门影响：** 如果有缺料风险，系统自动提示——这个信号也会流到生产部的齐套检查里。

---

### 生产部 —— 三个场景

#### 场景1：齐套欠料检查

```mermaid
flowchart LR
    subgraph 数据来源
        PLM_BOM[PLM BOM物料清单<br/>bom]
        ERP_INV[ERP 库存<br/>inventory]
        WMS_STOCK[WMS 仓储库存<br/>stock]
        MES_WO[MES 待投产工单<br/>work_orders]
    end

    subgraph 系统处理
        DC[数据适配层]
        CALC[按BOM算物料需求]
        GAP[算缺口<br/>需求 - 现有库存]
        WARN[缺料预警<br/>提前几天知道]
    end

    subgraph 生产部看到的
        REPORT[📋 缺口清单<br/>哪个料缺多少]
    end

    PLM_BOM --> DC
    ERP_INV --> DC
    WMS_STOCK --> DC
    MES_WO --> DC
    DC --> CALC --> GAP --> WARN
    WARN --> REPORT

    WARN -.->|缺料预警| SAL[📦 销售部<br/>交期答复]
    WARN -.->|缺料预警| BOSS[👔 厂长<br/>每日一页]
```

#### 场景2：管理每日一页

```mermaid
flowchart LR
    subgraph 数据来源
        MES_WO[MES 工单进度<br/>work_orders]
        MES_SHIFT[MES 报工记录<br/>shift_records]
        SCADA_ALARM[SCADA 设备报警<br/>alarms]
        QMS_DEFECT[QMS 质量不良<br/>defects]
    end

    subgraph 系统处理
        DC[数据适配层]
        AGG[汇总所有异常]
        RANK[按严重程度排序]
    end

    subgraph 生产部看到的
        DAILY[📊 每日一页<br/>今天该盯什么]
    end

    MES_WO --> DC
    MES_SHIFT --> DC
    SCADA_ALARM --> DC
    QMS_DEFECT --> DC
    DC --> AGG --> RANK --> DAILY

    DAILY -.->|全厂异常摘要| BOSS[👔 厂长<br/>首页看板]
```

#### 场景3：设备点检维保

```mermaid
flowchart LR
    subgraph 数据来源
        SCADA_EQUIP[SCADA 设备状态<br/>equipment]
        SCADA_ALARM[SCADA 报警记录<br/>alarms]
    end

    subgraph 系统处理
        DC[数据适配层]
        BOARD[设备看板<br/>红绿黄状态]
        MTBF[算运行时长<br/>什么时候该保养]
        SUGGEST[维修建议<br/>关联历史经验案例]
    end

    subgraph 生产部看到的
        ALERT[🔴 报警提醒]
        MAINTAIN[🔧 维保提醒]
    end

    SCADA_EQUIP --> DC
    SCADA_ALARM --> DC
    DC --> BOARD
    DC --> MTBF
    DC --> SUGGEST
    BOARD --> ALERT
    MTBF --> MAINTAIN
    SUGGEST --> MAINTAIN

    ALERT -.->|设备报警| BOSS[👔 厂长<br/>首页看板/通知]
    SUGGEST -.->|维修经验案例| DB[(SQLite 案例库)]
```

**生产部用户看到的：** 三个页面——齐套检查看缺料、每日一页看全厂异常、设备看报警和维保。

**跨部门影响：** 设备报警自动流到厂长首页和通知，缺料预警流到销售部影响交期答复。

---

### 质量部 —— 质量批次追溯

```mermaid
flowchart LR
    subgraph 数据来源
        QMS_INSP[QMS 检验记录<br/>inspections]
        QMS_DEFECT[QMS 不良记录<br/>defects]
        MES_WO[MES 生产工单<br/>work_orders]
        SCADA_EQUIP[SCADA 设备信息<br/>equipment]
    end

    subgraph 系统处理
        DC[数据适配层]
        TRACE[批次追溯<br/>哪台设备/哪个班次/哪个操作员]
        ROOT[根因分析<br/>关联设备/人员/班次]
    end

    subgraph 质量部看到的
        REPORT[🔍 追溯链路<br/>+ 根因结论]
    end

    QMS_INSP --> DC
    QMS_DEFECT --> DC
    MES_WO --> DC
    SCADA_EQUIP --> DC
    DC --> TRACE --> ROOT --> REPORT

    ROOT -.->|不良关联设备| PRO[🏗️ 生产部<br/>设备维保参考]
    ROOT -.->|质量异常| BOSS[👔 厂长<br/>首页看板]
```

**质量部用户看到的：** 客户投诉某批次有问题，输入批次号，系统自动追溯到是哪台设备、哪个班次、谁做的，根因是什么。

**跨部门影响：** 质量不良如果和设备有关，这个信号流到生产部的设备维保里——"这台设备做出来的东西老出问题"。

---

### 厂长 —— 首页总览

```mermaid
flowchart LR
    subgraph 所有部门汇总
        DASH[📊 首页看板<br/>全厂KPI一屏掌握]
    end

    subgraph 数据来源（全部汇总）
        ERP[ERP 订单/库存]
        MES[MES 工单/报工]
        SCADA[SCADA 设备]
        QMS[QMS 检验/不良]
    end

    subgraph 指标
        R1[订单完成率]
        R2[设备运行率/报警数]
        R3[质量合格率]
        R4[缺料预警数]
        R5[待审批数]
    end

    ERP --> DASH
    MES --> DASH
    SCADA --> DASH
    QMS --> DASH

    DASH --> R1
    DASH --> R2
    DASH --> R3
    DASH --> R4
    DASH --> R5

    DASH --> NOTIF[🔔 通知中心<br/>报警/审批/预警]
```

**厂长看到的：** 登录后一屏——订单完成率、设备运行率、质量合格率、缺料预警、待审批。5秒知道全厂今天状况。

---

### 管理员 —— 系统管理

```mermaid
flowchart LR
    subgraph 管理员操作
        UPLOAD[📁 数据上传<br/>CSV/Excel导入]
        RULES[📚 知识规则<br/>markdown版本管理]
        APPROVE[📋 待审批<br/>高风险动作审批]
        AUDIT[📝 审计日志<br/>所有操作留痕]
    end

    subgraph 系统
        DC[数据适配层<br/>切换mock→真实]
        KB[知识库Vault<br/>规则热加载]
        HR[人审闸门]
        LOG[审计日志文件]
    end

    UPLOAD --> DC
    RULES --> KB
    APPROVE --> HR
    AUDIT --> LOG
```

**管理员看到的：** 系统管理四个页面——传数据、管规则、审流程、看日志。

---

## 三、跨部门数据流总结

```mermaid
flowchart TB
    subgraph 生产部
        PRO_KIT[齐套检查]
        PRO_DAILY[每日一页]
        PRO_EQUIP[设备维保]
    end

    subgraph 质量部
        QC_TRACE[批次追溯]
    end

    subgraph 销售部
        SAL_DELIVERY[交期答复]
    end

    subgraph 财务部
        FIN_RECON[对账]
    end

    subgraph 厂长
        BOSS_DASH[首页看板]
    end

    PRO_KIT -.->|缺料预警| SAL_DELIVERY
    PRO_KIT -.->|缺料预警| BOSS_DASH
    PRO_DAILY -.->|全厂异常| BOSS_DASH
    PRO_EQUIP -.->|设备报警| BOSS_DASH
    PRO_EQUIP -.->|维修案例| QC_TRACE
    QC_TRACE -.->|不良关联设备| PRO_EQUIP
    FIN_RECON -.->|付款异常| BOSS_DASH
```

**关键跨部门流动：**
- **生产→销售：** 缺料预警影响交期答复
- **生产→厂长：** 每日异常汇总到首页
- **质量→生产：** 不良关联设备，反哺设备维保
- **财务→厂长：** 对账异常上通知
