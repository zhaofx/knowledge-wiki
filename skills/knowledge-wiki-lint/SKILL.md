---
name: knowledge-wiki-lint
description: Run a read-only health check of the local data-warehouse LLM Wiki at ${KNOWLEDGE_ROOT_DIR}/knowledge. Use when the user asks to “检查知识库”, “lint wiki”, “健康检查”, “查死链”, “检查孤岛页”, “知识库有没有问题”, “检查低置信度图片”, or wants a report of wiki quality issues. This skill must not modify files.
---

# Knowledge Wiki Lint

Use this skill for read-only wiki health checks.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/lint-wiki.md`.

## Workflow

Scan `wiki/` and relevant raw sidecar metadata, then produce a Markdown report with:

- dead links
- orphan pages
- contradictory statements
- missing concepts/entities
- review opportunities
- overlong pages
- tag issues
- low-confidence image sidecars
- top 3 recommended actions

## Remote source capture

Lint is read-only and should not fetch remote material by default. If a health-check finding requires a remote source to confirm whether local wiki/raw is stale, ask before pulling the remote source/result into `raw/`; otherwise report the missing/stale source as an action item.

## Boundaries

- Do not modify any file.
- For semantic checks, read relevant pages; do not rely only on filenames.
- If the wiki is large, sample intelligently and state the sampling strategy.
