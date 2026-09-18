# 制造业 AI Agent 落地平台 —— 技术分享

> 不是一个聊天框，而是一套能在企业里真正干活的岗位级系统。
> 核心设计原则：**懂公司 · 能办事 · 管得住 · 持续变强**。

---

## 一、这个系统在解决什么问题

工厂里的数据散在 ERP、MES、WMS、QMS、SCADA 里，问一次要找很多人；异常靠老师傅判断，口径不统一；报表能看到结果，却看不到过程和原因。

这个系统做的事：**让 AI 跨系统取数、按业务规则处理、把结论送回岗位，高风险动作留给人拍板。**

```mermaid
flowchart LR
    A["① 用户提问<br/>车间主任/计划员/老板<br/>「今天该盯什么？」"] --> B["② 意图识别<br/>关键词匹配<br/>MVP阶段可换LLM"]
    B --> C["③ 跨系统取数<br/>ERP + MES + WMS<br/>QMS + SCADA"]
    C --> D["④ 规则引擎分析<br/>业务规则+老师傅经验<br/>知识库RAG"]
    D --> E["⑤ 生成结论<br/>异常清单+建议动作<br/>按影响排序"]
    E --> F{"⑥ 人审闸门"}
    F -->|"低风险"| G["直接交付<br/>待办/工单/日报"]
    F -->|"高风险"| H["转人工审批<br/>付款/交期/停线/召回"]

    classDef ask fill:#e8d5f5,stroke:#9b59b6,stroke-width:2px
    classDef intent fill:#d5e8f5,stroke:#3498db,stroke-width:2px
    classDef data fill:#f5e0c5,stroke:#e67e22,stroke-width:2px
    classDef analyze fill:#f5e0c5,stroke:#e67e22,stroke-width:2px
    classDef deliver fill:#d5f5d5,stroke:#27ae60,stroke-width:2px
    classDef gate fill:#fff3cd,stroke:#f39c12,stroke-width:2px
    classDef human fill:#f5d5d5,stroke:#e74c3c,stroke-width:2px

    class A ask
    class B intent
    class C,D data
    class E deliver
    class F gate
    class G deliver
    class H human
```

---

## 二、系统分层架构

```mermaid
flowchart TB
    subgraph 交互层["交互层 — Streamlit 多页面"]
        UI1["6个场景页面"]
        UI2["待审批中心"]
        UI3["数据上传中心"]
        UI4["审计日志"]
    end

    subgraph 引擎层["引擎层 — Agent Engine"]
        E1["意图识别<br/>detect_intent()"]
        E2["技能路由<br/>register_skill()"]
        E3["人审闸门<br/>HumanReviewGate"]
    end

    subgraph 能力层["能力层 — Skills"]
        S1["采购对账"]
        S2["交期答复"]
        S3["管理日报"]
        S4["齐套欠料"]
        S5["设备维保"]
        S6["质量追溯"]
    end

    subgraph 数据层["数据层 — DataConnector"]
        D1["ERP适配器"]
        D2["MES适配器"]
        D3["WMS适配器"]
        D4["QMS适配器"]
        D5["SCADA适配器"]
    end

    subgraph 基础层["基础层 — 可复用底座"]
        B1["知识库 KnowledgeBase"]
        B2["审计 AuditLog"]
        B3["数据上传 DataStore"]
    end

    交互层 --> 引擎层
    引擎层 --> 能力层
    能力层 --> 数据层
    能力层 --> 基础层

    classDef ui fill:#d5e8f5,stroke:#3498db
    classDef engine fill:#e8d5f5,stroke:#9b59b6
    classDef skill fill:#d5f5d5,stroke:#27ae60
    classDef data fill:#f5e0c5,stroke:#e67e22
    classDef base fill:#f0f0f0,stroke:#7f8c8d

    class UI1,UI2,UI3,UI4 ui
    class E1,E2,E3 engine
    class S1,S2,S3,S4,S5,S6 skill
    class D1,D2,D3,D4,D5 data
    class B1,B2,B3 base
```

---

## 三、Agent 核心处理链路

每一个用户问题，都会走完以下 6 步：

```mermaid
flowchart LR
    A["① 接收问题<br/>用户自然语言输入<br/>记录提问时间"] --> B["② 意图识别<br/>关键词优先级匹配<br/>6个业务意图+兜底"]
    B --> C["③ 路由到技能<br/>调用对应skill handler<br/>传入engine上下文"]
    C --> D["④ 跨系统取数<br/>DataConnector统一入口<br/>上传文件优先→mock兜底"]
    D --> E["⑤ 规则分析<br/>业务规则+知识库经验<br/>计算异常/缺口/风险"]
    E --> F["⑥ 人审检查<br/>高风险动作拦截<br/>生成审批单"]

    classDef step fill:#e8d5f5,stroke:#9b59b6,stroke-width:2px
    class A,B,C,D,E,F step
```

**关键设计决策：**

| 设计点 | 做法 | 为什么 |
|--------|------|--------|
| 意图识别 | 关键词优先级匹配 | MVP零成本跑通，后续可无缝换LLM |
| 数据取数 | 上传文件 > mock数据 | 不用等真实系统，先跑流程再换数据 |
| 人审闸门 | 动作关键词匹配风险等级 | 高风险动作零漏网，低风险不卡流程 |
| 审计日志 | 每次ask独立session | 可回放、可审计、可追责 |
| 技能注册 | 装饰器式register_skill | 新增场景只加文件，不改引擎 |

---

## 四、数据层：统一入口，无缝切换

DataConnector 是所有数据的唯一入口。Agent 不直接碰底层系统，只调 `query_erp / query_mes / query_wms / query_qms / query_scada`。

```mermaid
flowchart LR
    A["Agent技能层"] --> B["DataConnector.query_xxx()"]
    B --> C{"有没有上传文件？"}
    C -->|"有"| D["读 uploaded_data/<br/>CSV/Excel<br/>真实数据"]
    C -->|"没有"| E["读 mock 模拟数据<br/>内置示例工厂"]
    D --> F["返回 list[dict]"]
    E --> F

    classDef agent fill:#e8d5f5,stroke:#9b59b6
    classDef conn fill:#d5e8f5,stroke:#3498db
    classDef decision fill:#fff3cd,stroke:#f39c12
    classDef live fill:#d5f5d5,stroke:#27ae60
    classDef mock fill:#f5d5d5,stroke:#e74c3c

    class A agent
    class B conn
    class C decision
    class D live
    class E mock
```

**支持的 10 张数据表：**

| 表名 | 来源系统 | 用途 |
|------|---------|------|
| `ERP_orders` | ERP | 销售订单 |
| `ERP_inventory` | ERP | 库存余额 |
| `ERP_purchase_orders` | ERP | 采购订单 |
| `ERP_ap_invoices` | ERP | 应付发票 |
| `MES_work_orders` | MES | 生产工单 |
| `WMS_stock` | WMS | 仓库库存+在途 |
| `QMS_inspections` | QMS | 检验记录 |
| `QMS_defects` | QMS | 不良记录 |
| `PLM_bom` | PLM | BOM清单 |
| `SCADA_equipment` | SCADA | 设备台账 |

---

## 五、六大场景技术实现

### 场景1：采购三单匹配对账

```mermaid
flowchart LR
    A["采购订单<br/>PO数据"] --> D["自动核对<br/>数量×金额"]
    B["收货记录<br/>GR数据"] --> D
    C["应付发票<br/>INV数据"] --> D
    D --> E["差异清单<br/>🔴金额差异>1%<br/>🟡未齐量"]
    E --> F["付款动作<br/>转财务审批"]

    classDef input fill:#d5e8f5,stroke:#3498db
    classDef process fill:#f5e0c5,stroke:#e67e22
    classDef output fill:#d5f5d5,stroke:#27ae60
    classDef review fill:#f5d5d5,stroke:#e74c3c

    class A,B,C input
    class D process
    class E output
    class F review
```

**核心逻辑：** 三单金额交叉核对，差异 >1% 标红，未齐量标黄。付款动作触发人审。

### 场景2：销售交期答复

```mermaid
flowchart LR
    A["销售订单"] --> D["综合判断<br/>物料齐套？<br/>完工率？"]
    B["库存+BOM"] --> D
    C["在制工单"] --> D
    D --> E["建议交期<br/>+风险提示"]
    E --> F["对外承诺<br/>转销售审批"]

    classDef input fill:#d5e8f5,stroke:#3498db
    classDef process fill:#f5e0c5,stroke:#e67e22
    classDef output fill:#d5f5d5,stroke:#27ae60
    classDef review fill:#f5d5d5,stroke:#e74c3c

    class A,B,C input
    class D process
    class E output
    class F review
```

**核心逻辑：** 物料缺口→等料到货；完工率≥80%→按计划完工日；待投产→需排产确认。

### 场景3-6：生产侧场景

| 场景 | 核心计算 | 关键输入 | 输出 |
|------|---------|---------|------|
| 齐套欠料 | `需求=BOM用量×数量 - (库存+在途)` | BOM/库存/在途/工单 | 缺料清单+影响工单 |
| 设备维保 | 报警匹配+运行时长阈值 | SCADA设备数据 | 风险分级+维修建议 |
| 质量追溯 | 批次正反向关联 | 检验/不良/设备/班次 | 追溯路径+根因 |
| 管理日报 | 多源异常聚合排序 | 工单/质量/设备/库存 | 一页纸异常清单 |

---

## 六、人审与审计：为什么这是"管得住"的关键

```mermaid
flowchart LR
    A["Agent建议动作"] --> B{"动作风险匹配？"}
    B -->|"付款/交期/停线/召回"| C["生成审批单<br/>指定审批人"]
    B -->|"低风险查询"| D["直接执行"]
    C --> E["人工批准/驳回"]
    E --> F["记录决策人+时间"]
    D --> G["全链路审计日志"]
    F --> G

    classDef ask fill:#e8d5f5,stroke:#9b59b6
    classDef decision fill:#fff3cd,stroke:#f39c12
    classDef review fill:#f5d5d5,stroke:#e74c3c
    classDef ok fill:#d5f5d5,stroke:#27ae60
    classDef audit fill:#f0f0f0,stroke:#7f8c8d

    class A ask
    class B decision
    class C,E review
    class D ok
    class F,G audit
```

**5类必须人审的动作（硬规则）：**

| 动作类型 | 审批人 | 对应场景 |
|---------|--------|---------|
| 对外承诺交期 | 销售负责人 | 交期答复 |
| 付款/折扣/退款 | 财务负责人 | 采购对账 |
| 停线/改排产/放行 | 生产负责人 | 齐套检查、设备维保 |
| 召回/判责/对外回复 | 质量负责人 | 质量追溯 |
| 越权访问/敏感审批 | 系统管理员 | 全局 |

---

## 七、从 Mock 到生产的落地路径

```mermaid
flowchart LR
    A["① 当前阶段<br/>Mock数据跑通<br/>验证流程"] --> B["② 上传Excel<br/>业务人员填模板<br/>用真实数据"]
    B --> C["③ 接系统API<br/>替换mock方法<br/>直连ERP/MES"]
    C --> D["④ 接LLM<br/>换语义意图识别<br/>更自然的对话"]
    D --> E["⑤ 接知识库RAG<br/>向量检索经验<br/>回答更内行"]

    classDef s1 fill:#d5e8f5,stroke:#3498db
    classDef s2 fill:#e8d5f5,stroke:#9b59b6
    classDef s3 fill:#d5f5d5,stroke:#27ae60
    classDef s4 fill:#f5e0c5,stroke:#e67e22
    classDef s5 fill:#f0f0f0,stroke:#7f8c8d

    class A s1
    class B s2
    class C s3
    class D s4
    class E s5
```

**第二步是最快见效的**：不需要改代码，在「数据上传」页面下载模板、填真实数据、上传即可。

**第三步的代码改动量**：只需改 `core/data_connector.py` 里的 `_load` 方法，把 `data_store.load_table()` 换成 API 调用，其他代码一行不动。

---

## 八、代码结构

```
E:\fde\
├── app.py                      # 主页（导航）
├── pages/                      # Streamlit多页面
│   ├── 1_💰_采购对账.py
│   ├── 2_📦_交期答复.py
│   ├── 3_📊_管理日报.py
│   ├── 4_📋_齐套检查.py
│   ├── 5_🔧_设备维保.py
│   ├── 6_🔍_质量追溯.py
│   ├── 7_📋_待审批.py
│   ├── 8_📝_审计日志.py
│   └── 9_📁_数据上传.py
├── core/
│   ├── agent_engine.py         # Agent引擎：意图→路由→执行→人审
│   ├── data_connector.py       # 数据连接层：上传优先→mock兜底
│   ├── data_store.py           # 上传文件管理+模板下载
│   ├── knowledge_base.py       # 知识库：规则+老师傅经验
│   ├── human_review.py         # 人审闸门
│   ├── audit_log.py            # 审计日志
│   └── ui_helpers.py          # 共享UI组件
├── skills/                     # 6个场景技能（每个一个文件）
├── uploaded_data/              # 用户上传的CSV数据
├── audit/                      # 审计日志输出
└── docs/
    └── implementation_guide.md  # 5个项目落地手册
```

---

## 快速启动

```bash
# 启动Web界面（用anaconda Python）
C:\Users\22397\anaconda3\python.exe -m streamlit run app.py

# 或命令行验证6个场景
python test_demo.py
```

浏览器打开 `http://localhost:8501`。
