---
name: knowledge-wiki-ingest
description: Ingest new material into the local data-warehouse LLM Wiki at ${KNOWLEDGE_ROOT_DIR}/knowledge. Use when the user wants to add a URL, Feishu/Lark document, business doc, metric dictionary, warehouse rule, table metadata, SQL, lineage, image, attachment, or other source into the knowledge base. Trigger for “摄取进知识库”, “放进知识库”, “导入知识库”, “把这个文档/URL/飞书资料加入我的知识库”, or “ingest”. Use sibling skills for ask/inbox/lint/digest/promote/merge.
---

# Knowledge Wiki Ingest

Use this skill to add new sources to the local data-warehouse wiki.

## Workspace

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## Required reads

1. Read `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`.
2. For URL/document ingestion, read `commands/ingest-url.md`.
3. For image ingestion, read `commands/ingest-image.md`.

## Raw landing rules

- Table metadata / DDL / schema / partitions / owners → `raw/tables/`
- Production SQL / DML / calculation SQL → `raw/sql/`
- Table or column lineage → `raw/lineage/`
- Metric dictionaries / metric exports → `raw/metrics/`
- Business docs / requirements / terms / processes → `raw/business/`
- Data warehouse rules / governance docs → `raw/rules/`
- Images / whiteboard exports / attachments → `raw/assets/`
- Unclassified notes → `raw/inbox/`

## Wiki landing rules

Compile stable reusable knowledge into:

- `wiki/overview/` for global business/warehouse overview
- `wiki/domains/` for business domains
- `wiki/metrics/` for indicators and calculation logic
- `wiki/tables/` for table index and selection rules
- `wiki/business/` for terms, entities, enums, processes
- `wiki/risks/` for caveats and review risks
- `wiki/rules/` for naming/modeling/partition/data-quality constraints

## Workflow

1. Preserve complete source text in the correct `raw/` location.
2. Do not overwrite existing raw facts without explicit user confirmation.
3. Extract only stable, reusable knowledge into `wiki/`.
4. Keep `wiki/index.md` in the data-warehouse entry structure.
5. Report created/updated raw and wiki paths.

## Defaults (do not ask)

These follow directly from `AIDE.md` §2/§3/§5 and must not be re-asked on every ingest:

- **Raw 保留完整原文 + Wiki 按主题拆多页**（`AIDE.md` §2.5「一个概念一个文件」+ §5.d step 3）。若信息量大，拆到 `wiki/overview/`、`wiki/metrics/`、`wiki/tables/`、`wiki/business/`、`wiki/risks/` 等对应目录，禁止把所有原子塞进单个大页。
- **Ingest 走 `raw → wiki` 直路，不自动写 `output/pending/`**（`AIDE.md` §3 三层不变式）。`pending` 只承接 `/promote` 出来的 QA 综述；ingest 结束即闭环，不需要征求"是否顺带生成 pending 候选"。
- **仅当以下情况才可以中断问询**：raw 落点在 §5.a 规则里存在多个合理候选、raw 主来源缺失导致必须标 `traceability: weak`、或用户显式要求进入 pending 流程。

## Remote source capture

If this workflow needs to call a remote knowledge source or platform tool — for example `lark_cli`, `search-doc`, `search-metric`, `search-hive-table`, `get_aeolus_info`, Hive metadata, task code, or lineage tools — and the source/result is not already in local `raw/`, handle it as follows:

- If the user explicitly asked to ingest/import/add it to the knowledge base, treat that as consent to save it.
- Otherwise ask before saving: `是否将读取到的原文/结果同步保存到知识库 raw 层？建议落点：raw/<category>/<path>。如果不同意，我只用于本次回答，不入库。`
- If the user agrees, save the full source/result under the correct `raw/` subdirectory with source metadata.
- If the user declines, do not write it to `raw/` or `wiki/`; use it only as transient context.

## Feishu/Lark sources

If the input is a Feishu/Lark URL, first use `lark_cli` or available document tools to fetch the full content, then continue the ingestion workflow here.

When the fetched document contains embedded resources, handle them as first-class raw assets:

- `<base_refer>` / `<bitable>` / `<sheet>`: read the referenced object and save the structure/results under `raw/metrics/` or the appropriate raw category.
- `<whiteboard>`: download the whiteboard thumbnail with `lark-cli docs +media-download --type whiteboard`, save it under `raw/assets/images/<source-slug>/`, and create a same-directory sidecar `.md` with token, source URL, extraction time, semantic notes, and parent document reference.
- `<img>` / `<image>`: download to `raw/assets/images/<source-slug>/` or the source document's `assets/` subdirectory, then create a sidecar `.md` when the image is information-dense.
- `<source>` / `<file>`: download to `raw/assets/files/<source-slug>/` and record it in the parent document manifest.

Update the parent raw document's `manifest.json` with every saved embedded resource path.
