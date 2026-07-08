---
name: knowledge-wiki-merge
description: Review and merge pending wiki candidates from ${KNOWLEDGE_ROOT_DIR}/knowledge/output/pending into the local data-warehouse wiki. Start with a grouped triage overview that summarizes candidates by recommendation (建议合并/建议编辑/建议跳过/建议拒绝) so users can avoid one-by-one fatigue. Bulk reject or bulk skip is allowed only for clearly low-value candidates after explicit user confirmation; bulk merge is never allowed. For every actual merge, show a concrete content summary and get explicit per-candidate user approval. Use when the user says “合并 pending”, “merge-pending”, “审批候选 wiki”, “把 pending 合进知识库”, or asks to review promoted candidates.
---

# Knowledge Wiki Merge

Use this skill to review and merge pending candidates into `wiki/`.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/merge-pending.md`.
3. List `output/pending/*.md` with `status: pending`.

## Workflow

Use a two-phase review flow to reduce approval fatigue while preserving the final safety gate for writes to `wiki/`.

### Phase 1: Triage overview

1. Scan all `output/pending/*.md` files whose frontmatter has `status: pending`.
2. For each candidate, read enough content to classify it: frontmatter, `摘要`, `要点`, source list, target path, and status flags. Do not classify from filename alone.
3. Assign exactly one recommendation:
   - `建议合并` — durable knowledge, reliable local sources, correct target path, low risk of polluting wiki
   - `建议拒绝` — auto-generated noise, low confidence, transient troubleshooting, transcript-only source, sensitive/irrelevant content, or not suitable for the data-warehouse wiki
   - `建议跳过` — potentially useful but needs later review, source ingestion, ownership decision, or better target placement
   - `建议编辑` — useful topic but candidate needs rewrite, de-duplication, source cleanup, target change, or sensitive-information removal before merge
4. Show a grouped overview before any per-candidate prompt:
   - counts by recommendation
   - for each candidate: index number, recommendation, one-line concrete summary, source class (`raw/wiki`, `transcript-only`, `mixed`, `remote-not-ingested`), confidence/status flags, and target path
5. Offer safe batch actions:
   - `bulk reject suggested rejects` — allowed only after user explicitly confirms; move all `建议拒绝` items to `_rejected/` with a shared reason plus per-file timestamp
   - `bulk skip suggested skips` — allowed only after explicit confirmation; leave files in pending and count them as skipped for this run
   - `review merge candidates` — enter Phase 2 for `建议合并` items
   - `review edit candidates` — enter Phase 2 for `建议编辑` items
   - `review all one by one` — enter Phase 2 in pending order
   - `stop` — make no changes

Bulk merge is intentionally not offered. A candidate entering `wiki/` becomes stable retrieval material, so every merge still needs its own approval.

### Phase 2: Per-candidate decision

For each selected candidate:

1. Read enough of the candidate body to understand its substance, not just frontmatter. If the candidate is long, read the frontmatter plus `摘要`, `要点`, `详情` headings, and source list.
2. Show a compact review card that includes:
   - pending file
   - target path
   - promoted source
   - candidate status flags such as `auto_generated`, `needs_review`, and `confidence` when present
   - concrete content summary in 3–5 lines, written in the user's language; do not use vague labels like “session summary” without explaining what the page actually says
   - key sources and whether they are local `raw/` / existing `wiki/` / transcript / remote URL
   - likely affected wiki pages
   - target existence check: whether `target_path` already exists and whether this is a new page or requires a merge/diff plan
   - explicit recommendation and 1–3 concise reasons
3. Ask the user for one explicit decision: `y`, `n`, `skip`, `edit`, or `stop`. Do not merge based on your recommendation alone.
4. Only on `y`, merge to `target_path`, update frontmatter, create `.merged` breadcrumb, and rebuild/update `wiki/index.md` preserving data-warehouse index structure.
5. On `n`, move to `output/pending/_rejected/` with reason.
6. On `skip`, leave the candidate unchanged in `output/pending/` and continue.
7. Report approved/rejected/skipped counts, including batch actions and per-candidate actions separately.

## Triage overview template

Use this shape before asking for any one-by-one decisions:

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

After the overview, ask which action to take:

```text
下一步？
1. 批量拒绝所有“建议拒绝”
2. 批量跳过所有“建议跳过”
3. 逐条审“建议合并”
4. 逐条审“建议编辑”
5. 逐条审全部
6. 停止
```

If the user chooses a batch reject/skip action, summarize exactly which files will be affected and ask for one more explicit confirmation before modifying files. However, if the user has already explicitly confirmed in plain text (for example: “确认批量拒绝”, “批量拒绝”, “按照你的建议批量拒绝”, “确认跳过这些建议跳过项”), treat that as the required confirmation and proceed directly; do not call `AskUserQuestion` again just to repeat the same confirmation.

## Review card template

Use this shape for every candidate before asking for a per-candidate decision:

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

If the candidate is auto-generated with low confidence, explain what it contains and normally recommend `建议拒绝` or `建议跳过` unless it has clear long-term value and clean local sources.

## Remote source capture

Before merging, check whether the candidate relies on remote sources that are not present under local `raw/`. If so, say this in the review card's `来源检查` and ask the user whether to fetch and save those sources/results into `raw/` before merge. If the user declines, either skip the candidate or merge only with an explicit note that the remote source was not ingested, according to the user's decision.

## Boundaries

- Never batch merge or batch approve into `wiki/`.
- Batch reject and batch skip are allowed only for grouped triage results and only after explicit user confirmation of the affected file list.
- Never merge before explicit per-candidate user approval for that candidate.
- Do not silently overwrite existing target pages; show a diff/merge plan first.
- Do not modify `raw/`.
