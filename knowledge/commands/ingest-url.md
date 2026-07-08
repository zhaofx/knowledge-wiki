---
description: 摄取一个 URL 到知识库，并编译进 wiki/
argument-hint: <url>
---

你将把一份新的网络来源摄取到本知识库。

URL：$ARGUMENTS

## 步骤

1. **抓取** URL（使用 WebFetch 或 curl），若抓取失败，再使用浏览器插件或Puppeteer/Playwright/web-access等工具先渲染再抓取。仍抓取失败，立即停止并报错——**不得臆造内容**。

2. **保存原始内容**：先按 `AIDE.md` §5.a 判断来源类型并选择 raw 落点：业务/需求/飞书文档优先写入 `raw/business/docs/<YYYY-MM-DD>-<slug>/index.md`，指标口径写入 `raw/metrics/<YYYY-MM-DD>-<slug>/index.md`，规范写入 `raw/rules/<YYYY-MM-DD>-<slug>/index.md`；无法判断时写入 `raw/inbox/<YYYY-MM-DD>-<slug>.md`。写入 Markdown 时加上 YAML frontmatter：
   ```yaml
   ---
   url: <原始 URL>
   title: <网页标题>
   author: <如有>
   fetched_at: <ISO 时间戳>
   ---
   ```
   保留清洗后的**完整正文**。此步骤**不得做摘要**。
   对于需要保存附件/图片的来源，优先使用**目录而非单文件**，因为第 2b 步可能会附带图片资源。

2b. **图片 → 侧车提取**（信息密集型网页的关键步骤）：
   - 把每个 `<img>` 下载到当前来源目录的 `assets/fig-N.<ext>`；若来源没有独立目录，则下载到 `raw/assets/images/<YYYY-MM-DD>-<slug>-fig-N.<ext>`。
   - 对每张图，调用 `/ingest-image <图片路径>`（或内联同样的逻辑——见 AIDE.md §14），生成一份**侧车**文件，内含 OCR 原文 + 语义描述 +（图表类）结构化数据或 mermaid DSL。
   - 在 `index.md` 中，把原先的 `![](assets/fig-N.png)` 替换为
     `[[fig-N]]` 双链，让图片成为**一等公民**。
   - **跳过**纯装饰图（logo、横幅、<10KB 的缩略图），仅在 `index.md` 里保留 `alt` 文本。

3. **执行摄取协议**（定义于 `AIDE.md` 第 5 节）：
   - 把内容拆成原子——概念、实体、论断。
   - 每个原子：合并到已有 `wiki/` 页面，或按第 4 节模板新建。
   - 每条论断必须带回指向第 2 步所保存文件的来源引用。

4. **反向链接扫描**：对每个新建的实体，扫描现有 wiki，将提到它的地方替换为 `[[双链]]`。

5. **重建** `wiki/index.md`。

6. **输出报告**，严格按以下格式：

   ```
   ## 摄取报告：<标题>

   - 原始文件：raw/<category>/<path>/index.md 或 raw/inbox/<file>.md
   - 抽取图片数：F（其中 F-low 条为低置信度，已标记待人工复核）
   - 新建页面（N）：
     - [[新页-1]] — 一句话理由
     - ...
   - 更新页面（M）：
     - [[已有页]] — 改了什么
     - ...
   - 新增双链数：K
   - 建议的延伸阅读：
     - <url 或概念> — 为什么
   ```

## 硬约束

- 禁止修改 `wiki/`、`raw/business/`、`raw/metrics/`、`raw/rules/`、`raw/assets/`、`raw/inbox/` 以外的任何文件；若要写入 `raw/tables/`、`raw/sql/`、`raw/lineage/`，必须是明确的表元数据/SQL/血缘摄取任务。
- 若已有页面名称相近但 slug/大小写不同，**必须询问**合并到哪一个，不得擅自创建重复页。
- 若来源需要付费或抓取为空，立即中止并报错，**不得编造**。
