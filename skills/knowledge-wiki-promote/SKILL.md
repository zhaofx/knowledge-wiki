---
name: knowledge-wiki-promote
description: Promote one or more saved Q&A artifacts under ${KNOWLEDGE_ROOT_DIR}/knowledge/output/qa into pending wiki candidates, or capture the current/last knowledge answer into QA first and then promote it. Use when the user says “把这次问答晋升”, “把上面那个沉淀”, “promote current/last”, “批量晋升这些 qa”, “这条回答值得沉淀”, “生成 pending 候选”, or provides output/qa/*.md paths, globs, or a QA directory to turn into long-lived wiki knowledge. This skill writes to output/qa/ as a recovery step and output/pending/, but never directly writes to wiki/.
---

# Knowledge Wiki Promote

Use this skill to transform saved Q&A artifacts into pending wiki candidates.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/promote.md`.
3. Resolve the requested QA inputs, then read each selected `output/qa/*.md` file; for `current`/`last`, use the current conversation context to create a recovery QA file first.

## Input resolution

Accept any of these inputs:

- A single QA file path under `output/qa/`.
- Multiple QA file paths separated by whitespace, newlines, commas, or bullets.
- A glob such as `output/qa/2026-06-10-*.md`.
- A directory under `output/qa/`, meaning all direct `*.md` QA files in that directory.
- Natural language such as “晋升今天的 QA” or “批量晋升最近 3 条”; resolve by listing matching files once and make one best-effort deterministic selection.
- `current`, `last`, `上一条`, `上面那个`, or “把刚才的问答晋升”: capture the most recent knowledge-style Q&A from the current conversation into `output/qa/<YYYY-MM-DD>-<slug>.md`, then promote that new QA file.

If no concrete QA input is supplied, do not open repeated per-file choice prompts. Read the recent `output/qa/*.md` candidates and list them once in a table with filename, `question` frontmatter or H1 title, `promote_candidate`, and a short description from `## 一句话回答` or `## 相对 wiki 的增量`. Then ask for a single text reply containing one or more filenames, a glob, or “all”.

## Recovery QA capture

Use this only when the user asks to promote `current`/`last`/“上面那个” and the relevant answer is not already in `output/qa/`.

1. Identify the most recent data-warehouse knowledge Q&A in the current conversation: the user's question, the assistant's final answer, any wiki/raw references, and any remote tool results used.
2. Write a QA artifact under `output/qa/<YYYY-MM-DD>-<slug>.md` using the AIDE.md QA template.
3. Set `promote_candidate: true` only when the recovered Q&A adds durable knowledge or a useful index page; otherwise set `false` and require explicit override before promotion.
4. If the recovered answer used remote platform/tool results that are not in local `raw/`, note that in `## 查阅到的来源` and `## 相对 wiki 的增量`, and expect the pending candidate to be `traceability: weak` until source ingestion is completed.
5. Continue into the normal batch workflow with the newly written QA file.

## Batch workflow

For each selected QA file:

1. Verify the source file is under `output/qa/`.
2. Skip files whose frontmatter has `promote_candidate: false`, unless the user explicitly asked to override.
3. Rewrite the conversational Q&A into a durable wiki-style page.
4. Preserve all sources and `[[双链]]` references.
5. Choose a target path according to AIDE.md wiki landing rules.
6. Write the candidate to `output/pending/<slug>.md` with required frontmatter:
   - `promoted_from`
   - `status: pending`
   - `target_path`
   - `traceability: strong|weak`
7. If the same pending slug already exists, diff-merge rather than overwriting unrelated content.

After processing all files, print one consolidated preview table with source QA, pending path, target path, traceability, and status (`created`, `merged`, `skipped`, or `failed`).

## Remote source capture

If any source Q&A cites remote material that is not stored in local `raw/`, do not ask once per file. Batch the affected sources into a single question: whether to fetch and save the remote originals/results into the appropriate `raw/` locations first. If the user declines, keep the remote citations explicit and mark those candidates as needing source ingestion before merge.

## Boundaries

- Do not write to `wiki/` in this skill.
- Do not modify source QA files except optionally adding `promoted_to: output/pending/<slug>.md`; in batch mode, update only files that were successfully promoted.
- Avoid interactive choice prompts for each QA file; batch selection and source-capture decisions into at most one clarification each.
- If `promote_candidate: false`, refuse or skip that file unless the user explicitly asks to override by editing the source metadata.
