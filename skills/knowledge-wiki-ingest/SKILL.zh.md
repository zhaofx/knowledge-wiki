---
name: knowledge-wiki-ingest
description: 把新素材摄取到 ${KNOWLEDGE_ROOT_DIR}/knowledge 下的本地数仓 LLM 知识库。触发场景包括用户希望把某个 URL、飞书 / Lark 文档、业务文档、指标字典、数仓规范、表元数据、SQL、血缘、图片、附件或其他来源加入知识库。触发词包括"摄取进知识库"、"放进知识库"、"导入知识库"、"把这个文档/URL/飞书资料加入我的知识库"、"ingest"等。查询 / inbox / lint / 综述 / 晋升 / 合并请使用同级 skill。
---

# Knowledge Wiki Ingest（知识摄取）

使用本 skill 把新来源加入本地数仓 wiki。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 对 URL / 文档类摄取，读取 `aide-commands/ingest-url.md`。
3. 对图片类摄取，读取 `aide-commands/ingest-image.md`。

## Raw 落点规则

- 表元数据 / DDL / schema / 分区 / 负责人 → `raw/tables/`
- 生产 SQL / DML / 计算 SQL → `raw/sql/`
- 表血缘或字段血缘 → `raw/lineage/`
- 指标字典 / 指标导出 → `raw/metrics/`
- 业务文档 / 需求 / 术语 / 流程 → `raw/business/`
- 数仓规范 / 治理文档 → `raw/rules/`
- 图片 / 白板导出 / 附件 → `raw/assets/`
- 无法分类的临时笔记 → `raw/inbox/`

## Wiki 落点规则

只把稳定、可复用的知识编译进：

- `wiki/overview/` 全局业务 / 数仓概览
- `wiki/domains/` 业务域
- `wiki/metrics/` 指标与计算逻辑
- `wiki/tables/` 表索引与选表规则
- `wiki/business/` 术语、实体、枚举、流程
- `wiki/risks/` 注意事项与审阅风险
- `wiki/rules/` 命名 / 建模 / 分区 / 数据质量约束

## 工作流

1. 将完整原文保存到正确的 `raw/` 位置。
2. 未经用户显式确认，不得覆盖已有 raw 事实。
3. 只从 raw 中抽取稳定、可复用的知识写入 `wiki/`。
4. 保持 `wiki/index.md` 的数仓入口结构。
5. 报告本次创建 / 更新的 raw、wiki 路径。

## 默认行为（不再询问）

以下默认行为直接源自 `AIDE.md` §2 / §3 / §5，属于硬规则，**每次 ingest 不得再问一遍**：

- **Raw 保留完整原文 + Wiki 按主题拆多页**（`AIDE.md` §2.5「一个概念一个文件」+ §5.d step 3）。信息量大时拆到 `wiki/overview/`、`wiki/metrics/`、`wiki/tables/`、`wiki/business/`、`wiki/risks/` 等对应目录，禁止把所有原子塞进单个大页。
- **Ingest 走 `raw → wiki` 直路，不自动写 `output/pending/`**（`AIDE.md` §3 三层不变式）。`pending` 仅承接 `/promote` 出来的 QA 综述；ingest 结束即闭环，不需要征求"是否顺带生成 pending 候选"。
- **只有在下列情况才允许中断问询**：raw 落点在 §5.a 规则里存在多个合理候选、raw 主来源缺失导致必须标 `traceability: weak`、或用户显式要求进入 pending 流程。

## 远端来源入库

若本工作流需要调用远端知识源或平台工具——例如 `lark_cli`、`search-doc`、`search-metric`、`search-hive-table`、`get_aeolus_info`、Hive 元数据、任务代码、血缘工具等——且相关来源/结果尚未在本地 `raw/`，按如下处理：

- 若用户明确要求"摄取 / 导入 / 加入知识库"，视为默认同意保存。
- 否则先确认：`是否将读取到的原文/结果同步保存到知识库 raw 层？建议落点：raw/<category>/<path>。如果不同意，我只用于本次回答，不入库。`
- 用户同意：将完整原文 / 结果保存到对应 `raw/` 子目录，并附来源元数据。
- 用户拒绝：不得写入 `raw/` 或 `wiki/`；仅作为临时上下文使用。

## 飞书 / Lark 来源

若输入是飞书 / Lark URL，先用 `lark_cli` 或可用的文档工具抓取完整内容，再继续本 skill 的摄取流程。

被抓回的文档中包含内嵌资源时，将其视为一等公民 raw 资产：

- `<base_refer>` / `<bitable>` / `<sheet>`：读取被引用对象，将结构 / 结果保存到 `raw/metrics/` 或合适的 raw 分类下。
- `<whiteboard>`：使用 `lark-cli docs +media-download --type whiteboard` 下载白板缩略图，保存到 `raw/assets/images/<source-slug>/`，并在同目录写侧车 `.md`，记录 token、来源 URL、抽取时间、语义说明、父文档引用。
- `<img>` / `<image>`：下载到 `raw/assets/images/<source-slug>/` 或对应源文档的 `assets/` 子目录；对信息密集型图片，再补一个同目录侧车 `.md`。
- `<source>` / `<file>`：下载到 `raw/assets/files/<source-slug>/`，并在父文档清单中记录。

每保存一个内嵌资源，都要更新父 raw 文档的 `manifest.json`。
