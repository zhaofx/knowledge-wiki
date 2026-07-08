---
name: knowledge-wiki-inbox
description: 处理位于 ${KNOWLEDGE_ROOT_DIR}/knowledge/raw/inbox 下的临时未分类材料，服务本地数仓 LLM 知识库。触发场景包括用户说"处理 inbox"、"清理 raw/inbox"、"整理知识库临时笔记"、"归档 inbox"、"把 inbox 里的材料编译进 wiki"等。本 skill 会依据 AIDE.md，把 inbox 条目分流到对应 raw 子目录，并把稳定知识编译进 wiki。
---

# Knowledge Wiki Inbox Processor（临时收件箱处理）

使用本 skill 处理 `raw/inbox/`。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/process-inbox.md`。
3. 检查 `${KNOWLEDGE_ROOT_DIR}/knowledge/raw/inbox/`（排除 `_archived/`）。

## 工作流

1. 列出 inbox 条目。
2. 逐条分类：业务文档、需求、术语/枚举、指标来源、规范、表元数据、SQL、血缘、附件、或不清楚。
3. 对分类明确的条目：把事实迁移或复制到对应 `raw/` 子目录；如有稳定知识可提炼，则同步编译到 `wiki/`。
4. 已处理的 inbox 文件归档到 `raw/inbox/_archived/`。
5. 分类模糊的条目保留在 inbox，并说明保留原因。
6. 重建/更新 `wiki/index.md`，保持数仓入口结构不变。

## 远端来源入库

若某条 inbox 只是远端指针，需读取本地 `raw/` 尚未收录的外部来源，在把完整原文/结果拉入 `raw/` 前先与用户确认。用户同意则按 raw 分流规则保存；不同意则不拉取，仅使用本地上下文处理，并在报告中说明"该远端来源未入库"。

## 安全

- 若单次归档条目将超过 20 条，先请求用户确认。
- 对模糊条目不要强行分类。
- 编译进 wiki 的内容必须保留来源标注。
