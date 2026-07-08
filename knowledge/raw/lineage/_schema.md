---
title: raw/lineage schema
type: schema
updated: 2026-07-07
---

# raw/lineage/ 层规范

存放**表级 / 字段级血缘 edge 快照**。
以增量、幂等 JSONL 为主；每条 edge 是一条**有向关系**，记录方向、层级、来源工具、采集时间。

## 目录布局

```
raw/lineage/
  _schema.md
  table_lineage_edges.json                # 主索引：表级 edges（JSONL 或 JSON 数组）
  column_lineage_edges.json               # 可选：字段级 edges
  by_guid/{guid}.json                     # 可选：某表一次 lineage 抓取的原始返回
```

## `table_lineage_edges.json` edge 结构

```json
{
  "from_qn": "tnscdm.dwd_tcs_task_di",
  "from_guid": "<upstream guid>",
  "to_qn": "tnscdm.ads_tcs_dp_prj_verifier_1d",
  "to_guid": "<current guid>",
  "direction": "upstream",
  "hop": 1,
  "edge_kind": "table_lineage",
  "via_task_guid": "<DoradoTask GUID>",
  "via_task_name": "<DoradoTask displayText>",
  "source_tool": "bytedcli hive lineage",
  "source_url": "https://data.bytedance.net/coral/lineage?guid=...",
  "captured_at": "2026-07-07T12:00:00+08:00",
  "captured_for": "tnscdm.ads_tcs_dp_prj_verifier_1d"
}
```

- **direction**：`upstream`（当前表读的表）| `downstream`（读当前表的表）| `peer`（不直接连当前表）
- **hop**：距离当前表的跳数；`hop=1` 为直接上下游，默认深度限制在 1
- **captured_for**：这一次抓取的**中心表** qualified_name；用于回查"为了谁抓的"
- **via_task_guid / via_task_name**：DataLeap 血缘拓扑是 `HiveTable → DoradoTask → HiveTable`，中间必经一个 Task 节点；折叠成 Hive→Hive 时保留 Task 引用便于反查具体调度任务
- **多 task 场景**：同一 Hive 表对可能通过多个 Task 连接，dedup 键为 `(from_guid, to_guid, edge_kind)`；只保留首个 task 的引用（后续 task 可通过 `raw/lineage/by_guid/*.json` 全量返回反查）

## 幂等追加规则

- edge 唯一键 = `(from_guid, to_guid, edge_kind)`
- 已存在的 edge 不重复插入；只更新 `captured_at` 与最大 `hop`
- 若 GUID 缺失，退化用 `(from_qn, to_qn, edge_kind)` 作唯一键并在 `notes` 记录

## `column_lineage_edges.json`（可选）

```json
{
  "from_qn": "tnscdm.dwd_tcs_task_di",
  "from_column": "close_time",
  "to_qn": "tnscdm.ads_tcs_dp_prj_verifier_1d",
  "to_column": "close_time",
  "transform": "identity|aggregate|expression",
  "captured_at": "...",
  "source_tool": "bytedcli hive lineage --column"
}
```

## 引用方式

- wiki 页面引用：`（来源：[[raw/lineage/table_lineage_edges.json]]）`
- grep 反查：按 `from_qn` / `to_qn` / `captured_for` 过滤
