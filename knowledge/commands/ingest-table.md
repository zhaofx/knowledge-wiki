---
description: 摄取一张 Hive/ClickHouse 表的元数据、DDL、血缘到 raw/，并更新 wiki/tables 索引
argument-hint: <db.table> [<db.table> ...] [--region cn] [--lineage-depth 1]
---

你将把一张远端仓库表**结构化地**摄取进本知识库。
目标 = raw 层落三类原子（元数据 / DDL / 血缘 edge），wiki 层只增一行 `table_index`。

参数：$ARGUMENTS

## 何时运行

- **显式**：用户调用 `/ingest-table <db.table>`；或用户在会话中要求"把 X 表放进知识库"、"补一下 Y 表的血缘"。
- **前置授权**：`bytedcli hive` 属于 AIDE.md §5.c 白名单内的远端知识能力；用户明示"摄取/放进知识库"即视为已授权，无需每张表再问。
- **默认参数**：`--region cn`、`--lineage-depth 1`（只拿直接上下游）。多张表用逗号或空格分隔。

## 步骤

### Step 1 — 定位表（search）

对每个 `db.table`：

```bash
bytedcli hive search --query <table> --type HiveTable --region <region>
```

- 从结果里定位一条命中，抽取 `guid`、`qualified_name`、`owner`。
- **多命中处理**：若同一 `table` 名在多个 db / region 下都命中，用 AskUserQuestion 让用户选，不得擅自选第一条。
- **未命中**：立即中止，报错 `TABLE_NOT_FOUND: <db.table> in <region>`；不做兜底猜测。
- 若要保留 search 原始返回：写入 `raw/tables/search_{keyword}_{YYYYMMDD}.json`（可选）。

### Step 2 — 表元数据（detail）

```bash
bytedcli hive detail <db> <table> --region <region>
```

- 写入 `raw/tables/by_table/{db}.{table}.json`，字段按 `raw/tables/_schema.md`。
- **必填**：`db / table / qualified_name / captured_at / source_tool: bytedcli hive detail / source_url`。
- 字段 `comment` 缺失时写 `null`，**不得虚构**。
- 追加/更新 `raw/tables/hive_tables_meta.json` 的索引行（若该批量索引存在）。

### Step 3 — DDL（ddl）

```bash
bytedcli hive ddl <db> <table> --region <region>
```

- 写入 `raw/sql/sql/{db}.{table}.ddl.sql`，文件头 4 行 SQL 注释 header：
  ```sql
  -- source_tool: bytedcli hive ddl
  -- source_url:  <DataLeap 表详情页 URL>
  -- captured_at: <ISO 时间戳>
  -- kind:        ddl
  ```
- SQL 主体逐字保留，禁止格式化。
- 追加一行到 `raw/sql/sql_index.json`：`{kind: "ddl", path, db, table, produces_tables: ["<qn>"], sha256, line_count, source_tool, captured_at}`。

### Step 4 — 血缘（lineage）

先确认 `guid` 已在 Step 2 拿到；否则用 `bytedcli hive detail` 补拿。

```bash
bytedcli --json hive lineage <guid> -d <lineage-depth>
```

**必须使用 `--json` 全局 flag**：TTY 输出会截断 relations 到 20 条（"... and N more relations"），只有 `--json` 才是完整数据。

- 完整 JSON 保存到 `raw/lineage/by_guid/{guid}.json` 作为原始快照。
- 把 `data.relations`（Hive→Task→Hive 双跳拓扑）**折叠成 Hive→Hive 单跳** edges 后展开：对每个 `DoradoTask` 节点，笛卡尔积它的 `inputs`（Hive→Task）与 `outputs`（Task→Hive）得到 Hive→Hive 边。
- 展开为 `raw/lineage/table_lineage_edges.json` 的一行，按 `raw/lineage/_schema.md` 结构；保留 `via_task_guid / via_task_name` 便于反查具体调度任务。
- **节点类型过滤（默认）**：**只保留 `HiveTable` 类型的 edge**，剥离 `ClickhouseTable / DoradoTask / DummyTable / DummyOutput` 等非表节点；Task 节点作为**折叠中介**必然会读到，但不作为 edge 端点。
- 用户显式指定 `--lineage-node-types HiveTable,ClickhouseTable` 时按传入白名单扩展端点类型。
- **幂等**：`(from_guid, to_guid, edge_kind)` 已存在时只更新 `captured_at` 与 `via_task_*`，不重复插入。
- **深度**：默认 `1`（只拿直接上下游）；用户显式指定 `--lineage-depth N` 时按 N 抓取。
- 抓取失败（如权限、超时）：不中止整个流程，只把该表的 lineage 标记为 `pending`，写一条 `retry_history` 记录到 `raw/lineage/_pending.json`。

### Step 5 — wiki 层落地

追加一行到 `wiki/tables/table_index.md`，格式对齐现有表：

```
| `{db}.{table}` | <层：ADS/DWS/DWD/DIM/ODS/...> | <粒度> | <时效：实时/小时/天> | <一句话用途> | <2–4 个关键字段> | <[[所在业务域]]> |
```

判断准则：
- 层从表名前缀推断（`ads_` / `dws_` / `dwd_` / `dim_` / `ods_`），无法判断写 `?` 并在下一次入库补。
- 用途从 `description` / `comment` 抽 1 句，超过 20 字截断；无 comment 时写 `<no comment>`。
- 关键字段：优先分区字段 + 高频维度键（含 `id / date / project_id / uuid` 等）。

**不新建单表详情页**：本命令**只更新索引行**，避免每张表都造一份稀疏的 `wiki/tables/{db}.{table}.md`。若用户后续要为该表做主维表决策 / 选表规则 / 口径解释，通过 `/ingest-url` 或人工写入 `wiki/tables/table_selection_guide.md`。

### Step 6 — 输出报告

```
## /ingest-table 报告

- 摄取表：N（成功 S，失败 F）
- 新增 raw 元数据：raw/tables/by_table/{db1}.{table1}.json ...
- 新增 DDL：raw/sql/sql/{db1}.{table1}.ddl.sql ...
- 新增 lineage edges：K（其中 pending P）
- table_index.md 追加行：R
- strong 溯源：X 张，weak：Y 张
- 建议后续：<如"跑 /ingest-url <飞书文档> 关联业务口径">
```

## 硬约束

- **禁止修改** `raw/business/`、`raw/metrics/`、`raw/rules/`、`raw/inbox/`、`wiki/` 除 `wiki/tables/table_index.md` 以外的任何文件。
- **禁止调用** `bytedcli hive create / modify / rows` 类**变更或副作用命令**；本命令是只读摄取。
- **禁止在** `raw/tables/by_table/*.json` 里**编造字段 comment**；远端没有就写 `null`。
- **禁止跳过** `captured_at / source_tool / source_url` 三元组；否则 traceability 直接判 `weak`。
- **禁止一次性摄取超过 20 张表**；超过则要求用户拆批，或先把清单写到 `raw/tables/search_*.json`，再逐张 detail/ddl/lineage。
- **禁止跨 region 混摄**；一次 `/ingest-table` 只跑一个 region，需要多 region 时另跑一次。

## 与其他命令的边界

| 场景 | 走哪个命令 |
|---|---|
| 只想快速看一眼表结构，不入库 | 直接跑 `bytedcli hive detail`；不写 raw |
| 想把一份口径 SQL / 生产 SQL 入库 | `/ingest-url` 或 `/ingest-file`（放 `raw/sql/` 里对应目录） |
| 想为某张已入库的表补业务语义 / 选表规则 | 走 `wiki/tables/table_selection_guide.md` 人工写入，或用 `/promote` 走 pending |
| 想批量摄取一整个 db | 先跑一次 `hive search --type HiveDB`，把清单存到 `raw/tables/search_*.json`，再分批 `/ingest-table` |
