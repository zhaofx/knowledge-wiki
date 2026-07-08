---
name: knowledge-wiki-ask
description: Query the local data-warehouse LLM Wiki at ${KNOWLEDGE_ROOT_DIR}/knowledge and close the knowledge loop by archiving the Q&A, noting raw-source capture status, and suggesting promotion when useful. Use when the user says “问我的知识库”, “查知识库”, “知识库里有没有”, “基于我的知识库回答”, asks which table/metric/business term/rule/risk is documented, or asks a knowledge question that should be answered from the local Aide 数仓知识库. This skill is for Q&A only; use sibling knowledge-wiki-* skills for ingest, inbox, lint, digest, promote, or merge.
---

# Knowledge Wiki Ask

Use this skill to answer questions from the local data-warehouse wiki.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/ask.md`.
3. Start from `${KNOWLEDGE_ROOT_DIR}/knowledge/wiki/index.md`.

## Workflow

1. Search `wiki/` first.
2. For table details, SQL truth, lineage, or raw metric sources, read only the minimal relevant files under:
   - `raw/tables/`
   - `raw/sql/`
   - `raw/lineage/`
   - `raw/metrics/`
3. Answer with inline wiki/raw references.
4. Archive the complete Q&A to `output/qa/<YYYY-MM-DD>-<slug>.md` as required by `ask.md`.
5. End the user-facing answer with a short knowledge-loop status: the QA archive path, whether any remote sources were saved to local `raw/`, and whether the answer is worth promoting.
6. Suggest `knowledge-wiki-promote` when the answer contains durable knowledge not yet captured in `wiki/`, or when the user likely expects the current answer to be promotable later.

## Remote source capture

If answering requires a remote knowledge source that is not already in local `raw/` — for example Feishu/Lark docs, `search-doc`, `search-metric`, `search-hive-table`, Aeolus metadata, Hive metadata, table tasks, task code, or lineage tools — ask the user before saving it into the knowledge base:

```text
我需要读取远端资料来回答这个问题。是否将读取到的原文/结果同步保存到知识库 raw 层？建议落点：raw/<category>/<path>。如果不同意，我只用于本次回答，不入库。
```

If the user agrees, save the full source/result under the correct `raw/` subdirectory before using it as durable knowledge. If the user declines, use it only for the current answer and explicitly say it was not stored in `raw/`. In both cases, record the raw capture status in the archived QA file and in the closing knowledge-loop status.

## Boundaries

- Do not write to `wiki/` in this skill.
- Do not read all of `raw/tables/`, `raw/sql/`, or `raw/lineage/`; use targeted lookup.
- If the wiki lacks information, say what raw source or platform lookup is needed.
