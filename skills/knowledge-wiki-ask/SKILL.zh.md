---
name: knowledge-wiki-ask
description: 查询位于 ${KNOWLEDGE_ROOT_DIR}/knowledge 的本地数仓 LLM 知识库，并完成知识闭环：归档问答、记录远端来源入库状态、必要时建议晋升。触发场景包括用户说"问我的知识库"、"查知识库"、"知识库里有没有"、"基于我的知识库回答"，或询问某张表 / 指标 / 业务术语 / 规范 / 风险是否在库，以及任何应该由本地 Aide 数仓知识库作答的问题。本 skill 只负责问答；摄取、inbox、lint、综述、晋升、合并请使用同级的 knowledge-wiki-* skill。
---

# Knowledge Wiki Ask（知识库问答）

使用本 skill 基于本地数仓 wiki 回答问题。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/ask.md`。
3. 从 `${KNOWLEDGE_ROOT_DIR}/knowledge/wiki/index.md` 入手检索。

## 工作流

1. 优先检索 `wiki/`。
2. 涉及表详情、SQL 真相、血缘、指标原始来源时，只按需读取最小相关文件：
   - `raw/tables/`
   - `raw/sql/`
   - `raw/lineage/`
   - `raw/metrics/`
3. 回答时对 wiki / raw 引用做行内标注。
4. 按 `ask.md` 要求，把完整问答归档到 `output/qa/<YYYY-MM-DD>-<slug>.md`。
5. 面向用户的答复末尾追加一段简短的"知识闭环状态"：QA 归档路径、本次是否将远端来源保存到本地 `raw/`、是否建议晋升。
6. 当回答包含尚未沉淀到 `wiki/` 的持久性知识、或用户后续可能希望晋升当前回答时，主动建议使用 `knowledge-wiki-promote`。

## 远端来源入库

若作答需要读取本地 `raw/` 尚未收录的远端来源——例如飞书 / Lark 文档、`search-doc`、`search-metric`、`search-hive-table`、Aeolus 元数据、Hive 元数据、表任务、任务代码、血缘工具等——在写入知识库前先向用户确认：

```text
我需要读取远端资料来回答这个问题。是否将读取到的原文/结果同步保存到知识库 raw 层？建议落点：raw/<category>/<path>。如果不同意，我只用于本次回答，不入库。
```

用户同意：先将完整原文/结果保存到对应 `raw/` 子目录，再作为持久性知识使用。
用户拒绝：仅用于本次回答，并在答复中显式说明"未保存到 `raw/`"。
两种情况都要在归档的 QA 文件里以及答复末尾的知识闭环状态中记录远端入库结果。

## 边界

- 本 skill 不得写入 `wiki/`。
- 不得全量读取 `raw/tables/`、`raw/sql/` 或 `raw/lineage/`；采用定向查找。
- 若 wiki 缺乏信息，明确说出还需要哪份 raw 来源或哪次平台查询才能补齐。
