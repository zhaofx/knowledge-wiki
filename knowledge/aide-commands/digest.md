---
description: 按周期或专题生成综述，写入 output/digests/
argument-hint: weekly | monthly | topic:<slug>
---

产出一份 Markdown 综述，覆盖一个范围窗口。对 `wiki/` 和 `raw/` 只读；只写
`output/digests/`。

入参：$ARGUMENTS

## 范围解析

- `weekly`         → 最近 7 天，按 `raw/*` 和 `wiki/*` 的 mtime
- `monthly`        → 最近 30 天
- `topic:<slug>`   → 从 `wiki/**/<slug>.md` 出发 2 跳可达的所有页面

入参为空时，默认走 `weekly`。

## 步骤

1. **解析范围**，得到一份具体文件清单。报告抬头要写明窗口
   （`window_from`、`window_to`）。

2. **组织章节**：

   ### 自上次综述以来的新增
   - 列出窗口内新增或更新的页面。
   - 格式：`[[页面]] —— 一句话说明改了什么`
   - 按类型分组（concepts / entities / topics）。

   ### 关键主题
   - 3–5 组相关页面聚类。
   - 每条：一句话定位 + 2–4 个 `[[双链]]`。
   - 优先挑选由 ≥3 个页面支撑的主题。

   ### 开放问题
   - 若存在 `wiki/topics/open-questions.md`，从中抽取。
   - 再加上范围内所有 `⚠️ 有争议：` 标记条目。

   ### 建议下一步阅读
   - 3 个候选。
   - URL 或来源来自 `raw/business/`、`raw/metrics/`、`raw/rules/` 等 frontmatter，挑那些已被引用但尚未被「深度整合」的（有 <3 个 wiki 页面引用）。

3. **写入** `output/digests/<YYYY-MM-DD>-<period>.md`，使用综述模板
   （AIDE.md §11.d）。 `topic:<slug>` 在文件名中 slug 化为 `topic-<slug>`。

4. **打印**新综述的路径，外加一行：
   `💡 分享到飞书：/export <path> --to lark`

## 硬约束

- 对 `wiki/` 和 `raw/` 只读。
- 不得把内容作为副作用推送进 `wiki/`。
- 即使范围内零变更，也要写一份「无动静」的综述——**一致性优先于偷懒**。
