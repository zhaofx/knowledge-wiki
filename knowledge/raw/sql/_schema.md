---
title: raw/sql schema
type: schema
updated: 2026-07-07
---

# raw/sql/ 层规范

存放**原始 SQL 真相源**：Hive DDL、生产任务 SQL、口径 DML。
永远不改写；`sql_index.json` 是 grep-friendly 的索引，`sql/*.sql` 是分文件本体。

## 目录布局

```
raw/sql/
  _schema.md
  sql_index.json                          # 索引：任务/表 → SQL 文件
  sql/
    {db}.{table}.ddl.sql                  # CREATE TABLE DDL
    {task_id}.{slug}.sql                  # 生产任务 SQL（若知任务 ID）
    {db}.{table}.{slug}.sql               # 口径 SQL / 探查 SQL（无任务 ID 时）
  <existing-doc-slug>/                    # 特例：文档配套的 SQL 集合（已存在）
    dashboard_sql.md
```

## `sql_index.json` 行结构（JSONL 或 JSON 数组均可）

```json
{
  "kind": "ddl|prod|dml|adhoc",
  "path": "raw/sql/sql/tnscdm.ads_tcs_dp_prj_verifier_1d.ddl.sql",
  "db": "tnscdm",
  "table": "ads_tcs_dp_prj_verifier_1d",
  "task_id": null,
  "produces_tables": ["tnscdm.ads_tcs_dp_prj_verifier_1d"],
  "reads_tables": [],
  "sha256": "<content sha256>",
  "line_count": 87,
  "source_tool": "bytedcli hive ddl",
  "source_url": "<DataLeap 表详情页 URL>",
  "captured_at": "2026-07-07T12:00:00+08:00"
}
```

**必填字段**：`kind / path / captured_at / source_tool`
**建议保留**：`produces_tables` 或 `reads_tables`（至少一项）、`sha256`

## 文件命名规范

| SQL 类型 | 命名 | 示例 |
|---|---|---|
| DDL | `{db}.{table}.ddl.sql` | `tnscdm.ads_tcs_dp_prj_verifier_1d.ddl.sql` |
| 生产任务 SQL（已知 task_id） | `{task_id}.{slug}.sql` | `12345678.tcs_pv_daily.sql` |
| 口径 SQL / 白皮书摘录 SQL | `{db}.{table}.{slug}.sql` | `tnscdm.ads_tcs_dp_project_1h.review_delay.sql` |
| ad-hoc / 探查 SQL | `adhoc/{YYYYMMDD}-{slug}.sql` | `adhoc/20260707-partition-probe.sql` |

## 内容硬约束

- 文件头必须保留一段 SQL 注释 header（不改写主体 SQL）：
  ```sql
  -- source_tool: bytedcli hive ddl
  -- source_url:  https://data.bytedance.net/coral/...
  -- captured_at: 2026-07-07T12:00:00+08:00
  -- kind:        ddl
  ```
- SQL 主体逐字保留；不得格式化、补注释、改大小写。
- 若 SQL 有敏感变量（token、pwd），用户需在入库前脱敏；本层不做自动脱敏。

## 引用方式

- wiki 页面引用：`（来源：[[raw/sql/sql/{db}.{table}.ddl.sql]]）`
- 表反查：`sql_index.json` grep `produces_tables` 或 `reads_tables`
