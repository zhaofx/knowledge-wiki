---
name: knowledge-wiki-merge
description: 审阅并把 ${KNOWLEDGE_ROOT_DIR}/knowledge/output/pending 下的候选合入本地数仓 wiki。以按推荐分组的三级总览开始（建议合并 / 建议编辑 / 建议跳过 / 建议拒绝），避免用户逐条疲劳。仅在用户显式确认后允许对明显低价值候选执行批量拒绝或批量跳过；批量合并任何时候都不允许。任何实际合并都必须先展示具体内容摘要，并逐条获取用户显式批准。触发场景包括用户说"合并 pending"、"merge-pending"、"审批候选 wiki"、"把 pending 合进知识库"、或希望审阅已晋升的候选。
---

# Knowledge Wiki Merge（候选合入）

使用本 skill 审阅并把 pending 候选合入 `wiki/`。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/merge-pending.md`。
3. 列出 `output/pending/*.md` 中 `status: pending` 的候选。

## 工作流

采用两阶段审阅流程：降低审批疲劳，同时保留写入 `wiki/` 前的最终安全闸门。

### 阶段一：分组总览

1. 扫描所有 frontmatter 中 `status: pending` 的 `output/pending/*.md` 文件。
2. 对每个候选，读取足以分类的内容：frontmatter、`摘要`、`要点`、来源列表、目标路径、状态标记。禁止只凭文件名分类。
3. 每个候选恰好赋一个推荐：
   - `建议合并` — 持久性知识、本地来源可靠、目标路径正确、污染 wiki 风险低
   - `建议拒绝` — 自动生成的噪声、置信度低、临时排障、只来自 transcript、涉敏 / 与主题无关、或不适合入数仓 wiki
   - `建议跳过` — 可能有用，但需要后续再审、来源尚需入库、需要归属决定、或需要更好的目标位置
   - `建议编辑` — 主题有用，但候选需要重写、去重、清洗来源、更换目标或去敏，才能合入
4. 在开始任何逐条询问之前，先展示分组总览：
   - 各推荐类型的数量
   - 逐条列出：序号、推荐、一句话具体摘要、来源类别（`raw/wiki`、`transcript-only`、`mixed`、`remote-not-ingested`）、置信度/状态标记、目标路径
5. 提供以下安全批量动作：
   - `bulk reject suggested rejects` — 仅在用户显式确认后允许；把所有 `建议拒绝` 项移动到 `_rejected/`，附共同原因和每个文件的时间戳
   - `bulk skip suggested skips` — 仅在显式确认后允许；文件保留在 pending，本轮计入 skipped
   - `review merge candidates` — 对 `建议合并` 项进入阶段二
   - `review edit candidates` — 对 `建议编辑` 项进入阶段二
   - `review all one by one` — 按 pending 顺序进入阶段二
   - `stop` — 不做任何变更

有意不提供批量合并。任何候选一旦进入 `wiki/` 就成为长期检索材料，每一次合并都必须独立获得批准。

### 阶段二：逐条决定

对每个进入阶段二的候选：

1. 阅读候选主体足以理解其内容，不能只看 frontmatter。候选较长时，读取 frontmatter 加 `摘要`、`要点`、`详情` 各标题下段落及来源列表。
2. 展示一张紧凑的审阅卡片，包含：
   - pending 文件
   - 目标路径
   - 晋升来源
   - 候选状态标记，如 `auto_generated`、`needs_review`、`confidence`（有则展示）
   - 3–5 行具体内容摘要，使用用户的语言；不要用"会话总结"这种模糊标签，必须说清楚这份页面到底讲了什么
   - 关键来源，及其属于本地 `raw/` / 已有 `wiki/` / transcript / 远端 URL 中哪一类
   - 可能波及的 wiki 页面
   - 目标存在性检查：`target_path` 是否已存在，本次是新建还是需要合并 / 展示 diff
   - 明确推荐 + 1–3 条精炼理由
3. 请求用户给出一个明确决策：`y`、`n`、`skip`、`edit`、`stop`。禁止仅凭 skill 的推荐就合并。
4. 只有在 `y` 时才：合并到 `target_path`，更新 frontmatter，创建 `.merged` 面包屑，并在保持数仓入口结构的前提下重建/更新 `wiki/index.md`。
5. `n`：移动到 `output/pending/_rejected/`，记录原因。
6. `skip`：候选保持在 `output/pending/` 不变，继续下一条。
7. 最终报告已批准 / 已拒绝 / 已跳过的数量，批量动作与逐条动作要分别统计。

## 总览模板

在开始任何逐条询问之前使用这种形式：

```text
## Pending 候选总览

总数：N
- 建议合并：A
- 建议编辑：B
- 建议跳过：C
- 建议拒绝：D

| # | 推荐 | 摘要 | 来源检查 | 状态 | 目标 |
|---|---|---|---|---|---|
| 1 | 建议拒绝 | 自动生成的 update-config hook 配置会话摘要 | mixed/transcript | auto=true, confidence=low | wiki/topics/... |
| 2 | 建议合并 | 举报成立量 SQL 口径，区分次数与对象量 | local raw/wiki | manual promote | wiki/metrics/... |
```

总览之后询问下一步动作：

```text
下一步？
1. 批量拒绝所有"建议拒绝"
2. 批量跳过所有"建议跳过"
3. 逐条审"建议合并"
4. 逐条审"建议编辑"
5. 逐条审全部
6. 停止
```

用户选择批量拒绝 / 跳过时，先复述将受影响的文件清单，再请求一次显式确认后再动手。但如果用户已经在自由文本中显式确认过（例如："确认批量拒绝"、"批量拒绝"、"按照你的建议批量拒绝"、"确认跳过这些建议跳过项"），视为已满足确认条件，直接执行；不要再用 `AskUserQuestion` 重复相同确认。

## 审阅卡片模板

在对每个候选做逐条决定前使用这种形式：

```text
── 候选 M / N ────────────────────────────
文件：        output/pending/<slug>.md
目标：        <target_path>
来源：        <promoted_from or sources summary>
状态：        auto_generated=<...>, confidence=<...>, needs_review=<...>
目标检查：    <不存在，新建 | 已存在，需要合并/展示 diff | 路径不合适>
内容摘要：
  1. <candidate actually says ...>
  2. <main durable facts or workflow ...>
  3. <scope and caveats ...>
来源检查：    <local raw/wiki ok | transcript-only | remote not ingested | mixed>
可能波及：    <wiki pages likely affected>
推荐：        <建议合并/建议拒绝/建议跳过/建议编辑>
理由：        <1–3 short reasons>
──────────────────────────────────────────
批准吗？[y/n/skip/edit/stop]
```

若候选是自动生成且置信度低，说明其内容后，默认推荐 `建议拒绝` 或 `建议跳过`；除非它显然有长期价值且来源干净可靠，才可推荐合并。

## 远端来源入库

合并前，检查候选是否依赖本地 `raw/` 下不存在的远端来源。若是，在审阅卡片的"来源检查"里说明，并请求用户是否先把这些原文/结果抓入 `raw/` 再合并。用户拒绝时，按用户决定跳过该候选、或在合并时显式标注"远端来源未入库"。

## 边界

- 绝不批量合入 `wiki/`。
- 批量拒绝、批量跳过只允许基于分组总览的结果，且必须在用户显式确认受影响文件清单后执行。
- 无候选独立批准，绝不合并该候选。
- 不得静默覆盖已有目标页；先展示 diff / 合并计划。
- 不得修改 `raw/`。
