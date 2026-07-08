---
name: knowledge-wiki-digest
description: Generate a weekly, monthly, or topic digest for the local data-warehouse LLM Wiki at ${KNOWLEDGE_ROOT_DIR}/knowledge. Use when the user says “生成知识库周报/月报”, “digest”, “知识库综述”, “总结最近知识库变化”, “这个 topic 做个综述”, or asks for a period/topic summary. Writes only to output/digests/.
---

# Knowledge Wiki Digest

Use this skill to generate digest artifacts.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/digest.md`.

## Inputs

- `weekly` by default
- `monthly`
- `topic:<slug>`

## Workflow

1. Determine the window or topic scope.
2. Read relevant `wiki/` pages and recent `raw/` sources.
3. Write one digest file to `output/digests/<YYYY-MM-DD>-<period>.md`.
4. Include:
   - new/updated pages
   - key themes
   - open questions
   - recommended next reading
5. Print the digest path.

## Remote source capture

Digest generation should primarily use local `wiki/` and `raw/`. If you decide a remote source is needed to explain a change or fill a gap, ask before saving its source/result into `raw/`. If the user declines, use only local content or clearly mark the remote material as not ingested.

## Boundaries

- Do not write to `wiki/`.
- Do not push to Feishu automatically.
- Even for zero changes, write a “no material changes” digest for consistency.
