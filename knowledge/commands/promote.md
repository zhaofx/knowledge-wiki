---
description: 把一个或多个 qa 回答批量晋升为待审批的候选 wiki 页面
argument-hint: <qa 文件路径、多个路径、glob、目录、all、current 或 last>
---

用户希望把一次或多次历史问答晋升为 wiki 候选。

qa 输入：$ARGUMENTS

## 输入解析

`$ARGUMENTS` 支持：

- 单个 `output/qa/*.md` 文件。
- 多个 `output/qa/*.md` 文件，使用空格、换行、逗号或项目符号分隔。
- glob，例如 `output/qa/2026-06-10-*.md`。
- `output/qa/` 下的目录，表示该目录直接包含的全部 `*.md`。
- `all`，表示 `output/qa/` 下全部直系 `*.md`。
- “今天的 QA”“最近 3 条”等自然语言范围；先按文件名/mtime 做确定性解析。
- `current`、`last`、`上一条`、`上面那个`、`刚才的问答`：如果相关问答尚未存在于 `output/qa/`，先从当前会话恢复生成一个 QA 文件，再继续晋升。

若 `$ARGUMENTS` 为空或无法解析，不要逐条弹窗追问。读取最近候选 QA，并只展示一次候选表格：包含文件名、frontmatter `question` 或 H1 标题、`promote_candidate`、以及来自 `## 一句话回答` 或 `## 相对 wiki 的增量` 的简短描述；然后请求用户用一条文本回复提供文件名、多个文件名、glob 或 `all`。

## 步骤

1. **解析输入**
   - 若输入指向已有 QA 文件、glob、目录或 `all`，解析并读取所有选中的 QA 文件。
   - 若输入是 `current` / `last` / `上一条` / `上面那个` / `刚才的问答`，先识别当前会话中最近一次知识型问答，按 AIDE.md §11.b 写入 `output/qa/<YYYY-MM-DD>-<slug>.md`，再把该新 QA 文件加入晋升列表。
   - 每个最终晋升源都必须在 `output/qa/` 下，否则该文件标记为 `failed`，继续处理其他文件。

2. **恢复 QA 的要求**
   - 恢复文件必须包含原问题、完整回答、查阅到的 wiki/raw/远端工具来源、以及相对 wiki 的增量。
   - 若用了尚未保存到 `raw/` 的远端工具结果，在 QA 中明确标注“远端结果未入库”。
   - 只有当内容具备长期沉淀价值时才设 `promote_candidate: true`；否则设为 `false`，需要用户明确覆盖才继续晋升。

3. **改写，而非复制**
   - 源是对话产物。目标必须是一篇正式 wiki 页面（见 AIDE.md §4）。
   - 用**第三人称、无时态**语气改写，剥离「你问我答」的脚手架。
   - 提炼有长期价值的综合，丢掉聊天骨架。
   - 完整保留 `[[双链]]` 和所有来源。

4. **提议落位**
   - 默认：`wiki/topics/<slug>.md`
   - 若只是单一概念：建议 `wiki/concepts/<slug>.md`
   - 若主要讲实体：建议 `wiki/entities/...`
   - 若多条 QA 属于同一稳定主题，可以各自生成候选；不要未经用户确认把语义不同的 QA 强行合成一个页面。

5. **写入 pending**
   - 路径：`output/pending/<slug>.md`
   - frontmatter **必须**包含：
     ```yaml
     promoted_from: <qa 文件路径>
     status: pending
     target_path: <提议的 wiki 路径>
     traceability: strong | weak
     ```
   - 若同名 slug 的 pending 已存在，做 diff-merge，不要覆盖无关内容。

6. **批量预览**
   - 打印一个汇总表：
     ```text
     | 来源 QA | pending 路径 | 目标位置 | traceability | 状态 |
     |---|---|---|---|---|
     ```
   - 下面再列出所有引用的 `[[双链]]` 去重集合。

7. **不要**写入 `wiki/`。那一步只在 `/merge-pending` 里发生。

## 远端来源处理

如果多个 QA 引用了尚未进入本地 `raw/` 的远端材料，不要逐条询问。先汇总远端来源和建议 raw 落点，再一次性询问用户是否 capture。若用户不同意，候选仍可写入 `output/pending/`，但应标记 `traceability: weak`，并在正文中注明 merge 前需要补充 source ingestion。

## 硬约束

- 任何不在 `output/qa/` 下的输入都不得晋升。
- 若某个 qa 的 frontmatter 有 `promote_candidate: false`，默认跳过该文件并在汇总表说明；除非用户明确要求覆盖。
- 不得修改源 qa 文件，**除非**是为成功晋升的源文件 frontmatter 加上
  `promoted_to: output/pending/<slug>.md` 这一行。
- 批量模式下不要对每个文件弹确认框；最多一次性澄清输入范围、一次性澄清远端来源 capture。
