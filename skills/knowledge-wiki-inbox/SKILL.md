---
name: knowledge-wiki-inbox
description: Process unclassified temporary material in ${KNOWLEDGE_ROOT_DIR}/knowledge/raw/inbox for the local data-warehouse LLM Wiki. Use when the user says “处理 inbox”, “清理 raw/inbox”, “整理知识库临时笔记”, “归档 inbox”, “把 inbox 里的材料编译进 wiki”, or similar. This skill classifies inbox items into raw subdirectories and/or compiles stable knowledge into wiki according to AIDE.md.
---

# Knowledge Wiki Inbox Processor

Use this skill to process `raw/inbox/`.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/process-inbox.md`.
3. Inspect `${KNOWLEDGE_ROOT_DIR}/knowledge/raw/inbox/` excluding `_archived/`.

## Workflow

1. List inbox entries.
2. Classify each item as business doc, requirement, term/enum, metric source, rule, table metadata, SQL, lineage, asset, or unclear.
3. For clear items, move or copy facts into the appropriate `raw/` subdirectory and compile stable knowledge into `wiki/` if useful.
4. Archive processed inbox files to `raw/inbox/_archived/`.
5. Leave unclear items in inbox and report why.
6. Rebuild/update `wiki/index.md` while preserving the data-warehouse entry structure.

## Remote source capture

If an inbox item is only a remote pointer and requires reading an external source that is not already in local `raw/`, ask before pulling the full source/result into `raw/`. If the user agrees, save the fetched material according to the raw landing rules; if not, leave the item or process only local context and report that the remote source was not ingested.

## Safety

- If more than 20 inbox entries would be archived, ask the user for confirmation first.
- Do not force-classify ambiguous notes.
- Preserve source attribution in wiki pages.
