---
title: raw/tables schema
type: schema
updated: 2026-07-07
---

# raw/tables/ 层规范

存放 Hive / ClickHouse / Doris 等仓库表的**结构化元数据快照**。
只读、可覆盖；每次远端摄取即为新一次 snapshot，允许覆盖旧文件。

## 目录布局

```
raw/tables/
  _schema.md                              # 本文件
  by_table/{db}.{table}.json              # 单表元数据（首选粒度）
  by_table/{db}.{table}.stats.json        # 可选：分区行数等 stats
  hive_tables_meta.json                   # 可选：批量索引（多张表汇总）
  search_{keyword}_{YYYYMMDD}.json        # 可选：一次 search 的原始返回
```

## `by_table/{db}.{table}.json` 结构

```json
{
  "db": "tnscdm",
  "table": "ads_tcs_dp_prj_verifier_1d",
  "qualified_name": "tnscdm.ads_tcs_dp_prj_verifier_1d",
  "guid": "<DataLeap GUID>",
  "region": "cn",
  "owner": "<owner user id or dept>",
  "layer": "ADS|DWS|DWD|DIM|ODS|APP|BMQ|Other",
  "storage_format": "PARQUET|ORC|TEXT|Other",
  "ttl_days": 90,
  "life_cycle": "hot|warm|cold|permanent",
  "partitions": [
    {"name": "date", "type": "string", "comment": "分区日期 yyyymmdd"}
  ],
  "columns": [
    {
      "name": "project_id",
      "type": "bigint",
      "comment": "队列 ID",
      "is_partition": false,
      "is_nullable": true
    }
  ],
  "description": "<表级 comment 原文>",
  "asset_url": "https://data.bytedance.net/coral/asset_detail?guid=...",
  "source_tool": "bytedcli hive detail",
  "source_url": "<DataLeap 表详情页 URL>",
  "captured_at": "2026-07-07T12:00:00+08:00",
  "captured_by": "knowledge-wiki-ingest",
  "raw_response_path": "raw/tables/by_table/tnscdm.ads_tcs_dp_prj_verifier_1d.raw.json"
}
```

**必填字段（strong traceability 门槛）**：
`db / table / qualified_name / captured_at / source_tool / source_url`

**建议保留字段**：`columns[].comment`、`partitions`、`ttl_days`、`asset_url`。
`comment` 缺失时不得虚构，可写 `null`。

## `hive_tables_meta.json` 结构（批量索引）

```json
{
  "generated_at": "2026-07-07T12:00:00+08:00",
  "tables": [
    {
      "qualified_name": "tnscdm.ads_tcs_dp_prj_verifier_1d",
      "guid": "...",
      "owner": "...",
      "path": "raw/tables/by_table/tnscdm.ads_tcs_dp_prj_verifier_1d.json"
    }
  ]
}
```

## 命名与幂等约束

- 文件名统一 `{db}.{table}.json`，全小写。
- 覆盖旧文件即为**新的 snapshot**，同时更新 `captured_at`。
- 不得删除历史 snapshot 以外的字段；若字段消失，改写为 `null` 并在 `notes[]` 记录变更。

## 引用方式

- wiki 页面引用：`（来源：[[raw/tables/by_table/{db}.{table}.json]]）`
- 血缘反查：通过 `guid` 关联 `raw/lineage/table_lineage_edges.json`
- SQL 反查：通过 `qualified_name` 关联 `raw/sql/sql_index.json`
