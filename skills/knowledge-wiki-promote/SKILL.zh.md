---
name: knowledge-wiki-promote
description: 把 ${KNOWLEDGE_ROOT_DIR}/knowledge/output/qa 下已归档的 Q&A 晋升为待合入 wiki 候选（pending），或先将当前 / 上一条对话中的问答回捞成 QA 再晋升。触发场景包括用户说"把这次问答晋升"、"把上面那个沉淀"、"promote current/last"、"批量晋升这些 qa"、"这条回答值得沉淀"、"生成 pending 候选"，或直接提供 output/qa/*.md 路径、glob、或某个 QA 目录，用于把可复用知识落到 wiki。本 skill 会写入 output/qa/（作为回捞补写步骤）和 output/pending/，但绝不直接写 wiki/。
---

# Knowledge Wiki Promote（问答晋升）

使用本 skill 把已归档的 Q&A 转换为待合入 wiki 的候选。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/promote.md`。
3. 先解析用户提供的 QA 输入，再逐一读取被选中的 `output/qa/*.md`；若输入是 `current` / `last`，则先根据当前会话上下文回捞出一份 QA 文件。

## 入参解析

支持以下任意一种输入形式：

- 一个位于 `output/qa/` 下的 QA 文件路径。
- 用空白、换行、逗号或项目符号分隔的多个 QA 文件路径。
- glob 例如 `output/qa/2026-06-10-*.md`。
- `output/qa/` 下的一个目录，表示该目录下所有直接 `*.md` QA 文件。
- 自然语言，例如"晋升今天的 QA"、"批量晋升最近 3 条"；先一次性列出匹配文件，再做一次尽力而为、可确定复现的选择。
- `current`、`last`、`上一条`、`上面那个`、"把刚才的问答晋升"：先从当前会话中把最近一段知识型 Q&A 回捞成 `output/qa/<YYYY-MM-DD>-<slug>.md`，然后把这份新写的 QA 走正常晋升流程。

若用户未给出明确 QA 输入，不要对每个文件反复弹选择框。读取近期 `output/qa/*.md`，一次性列出候选表，包含文件名、`question` frontmatter 或一级标题、`promote_candidate`、以及从 `## 一句话回答` 或 `## 相对 wiki 的增量` 提取的简短说明。随后请求用户用一次性文本回复给出一个或多个文件名 / glob / `all`。

## 会话回捞 QA

仅当用户要求晋升 `current` / `last` / "上面那个"，且相关回答尚未落地到 `output/qa/` 时，才走该路径。

1. 识别当前会话中最近一段数仓知识型 Q&A：用户问题、助手最终答复、涉及的 wiki/raw 引用、以及使用过的远端工具结果。
2. 按 AIDE.md 的 QA 模板，把回捞产物写入 `output/qa/<YYYY-MM-DD>-<slug>.md`。
3. 仅当回捞出的 Q&A 确实新增了持久性知识或有用索引页时，才设 `promote_candidate: true`；否则设为 `false`，除非用户显式覆盖，否则不进入晋升。
4. 若回捞回答用到了尚未入本地 `raw/` 的远端平台/工具结果，在 `## 查阅到的来源` 和 `## 相对 wiki 的增量` 里如实注明，并预期该 pending 候选默认 `traceability: weak`，直到来源被入库。
5. 用这份新写好的 QA 文件继续走下面的批处理工作流。

## 批处理工作流

对每个被选中的 QA 文件：

1. 校验源文件位于 `output/qa/` 下。
2. 若 frontmatter 中 `promote_candidate: false`，跳过；除非用户显式要求覆盖。
3. 将会话式 Q&A 改写成持久性、可复用的 wiki 风格页面。
4. 完整保留所有来源和 `[[双链]]` 引用。
5. 依 AIDE.md 的 wiki 落点规则选定目标路径。
6. 写入 `output/pending/<slug>.md`，包含以下必须字段：
   - `promoted_from`
   - `status: pending`
   - `target_path`
   - `traceability: strong|weak`
7. 若目标 pending slug 已存在，做 diff 合并，不能直接覆盖无关内容。

处理完全部文件后，统一打印一张预览表：源 QA、pending 路径、目标路径、traceability、以及状态（`created` / `merged` / `skipped` / `failed`）。

## 远端来源入库

若被选中的任一 QA 引用了未入本地 `raw/` 的远端材料，不要逐个文件反复询问。将受影响的来源合并成一个问题：是否先把这些远端原文/结果一次性抓回并保存到对应的 `raw/` 位置。用户拒绝时，保留引用原样，并把这些候选标记为"合入前需要先补入来源"。

## 边界

- 本 skill 不得写入 `wiki/`。
- 除非是为已成功晋升的文件追加 `promoted_to: output/pending/<slug>.md`，否则不要修改源 QA 文件；批处理场景下也只更新成功晋升的那部分文件。
- 避免对每个 QA 弹独立选择框；候选选择与来源入库决策各自最多合并成一次澄清。
- 若源文件 `promote_candidate: false`，除非用户要求手工编辑该字段以显式覆盖，否则拒绝或跳过该文件。
