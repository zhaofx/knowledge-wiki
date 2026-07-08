---
description: 从一张图片中抽取知识，在图片同目录生成一个侧车 .md
argument-hint: <图片路径或 URL>
---

从图片中抽取其承载的知识，并在图片同目录**生成一份侧车 Markdown**，让图像内容成为知识库里的**一等公民**（可检索、可引用、可 lint）。

来源：$ARGUMENTS

## 何时运行

- **显式**：用户调用 `/ingest-image <路径>`。
- **隐式**：`/ingest-url` 在遇到非装饰性 `<img>` 时会自动调用此命令。

## 图片分类（从下表中选一项）

| 类型 | 示例 | 抽取策略 |
|---|---|---|
| `text-screenshot`  | 公众号 / PPT / 论文截图 | OCR 文字提取 |
| `infographic`      | 图 + 说明 / 标注的信息图 | OCR + VLM 语义摘要 |
| `chart`            | 柱状 / 折线 / 饼图 | VLM → 还原为 Markdown 表格 |
| `diagram`          | 流程图 / 架构图 | VLM → 还原为 `mermaid` DSL |
| `whiteboard`       | 手写白板 | 手写 OCR；低置信度需标记 |
| `formula`          | 数学 / 物理公式 | Mathpix / Nougat → LaTeX |
| `code-screenshot`  | 代码截图 | OCR → 代码块 + 语言识别 |
| `decorative`       | 横幅 / 装饰插图 | **跳过**，仅保留父文档 `alt` |

若判定为 `decorative`，立即停止并返回 `skipped: decorative`。

## 步骤

1. **解析输入**
   - 若 `$ARGUMENTS` 是 URL，先下载到 `raw/assets/images/<YYYY-MM-DD>-<slug>/`，或当前来源目录的 `assets/` 子目录。
   - 若是本地路径，校验其必须位于 `raw/` 之下（否则拒绝执行）。

2. **分类**（见上表）。把分类写入侧车 frontmatter。

3. **按策略抽取**：
   - **OCR 层**（始终做）：提取所有可辨识字符，按阅读空间顺序保留。**不得改写**。
   - **语义层**（始终做）：1–2 段描述图像在传递什么信息。
   - **结构化层**（按类型）：
     - `chart` → 一张 Markdown 表格，按图中轴与数值还原。
     - `diagram` → 一段 `mermaid` 代码块（flowchart / sequence / …）。
     - `formula` → 一段 LaTeX。
     - `code-screenshot` → 带语言标识的代码块。
     - `text-screenshot` / `whiteboard` → 省略此层。

4. **实体扫描**
   - 抽出图中每个独立实体（人、组织、产品、概念）。
   - 对每个实体检查 `wiki/entities/` 或 `wiki/concepts/` 是否已有页面——若有，用 `[[双链]]` 引用。

5. **写侧车**到图片同目录，文件名与图片同名，扩展改为 `.md`：

   ```markdown
   ---
   type: figure
   source_image: assets/fig-N.<ext>
   image_class: chart | diagram | text-screenshot | ...
   extracted_at: <ISO 时间戳>
   extractor: vlm-aide | ocr-paddle | mathpix | ...
   confidence: high | medium | low
   entities:
     - [[concepts/xxx]]
     - [[entities/people/yyy]]
   ---

   # 图 N — <从标题或内容推断的短标题>

   ## OCR 原文
   <逐字 OCR，按空间顺序>

   ## 语义描述
   <1–2 段说明图在传递什么>

   ## 结构化数据
   <表格 / mermaid / latex / 代码块——仅在适用时出现>

   ## 出现位置
   - [[raw/business/docs/<slug>/index.md]] 或其他父级 raw 文档 —— 章节 / 上下文
   ```

6. **低置信度标记**
   - 若 OCR 置信度低（模糊、花体字、手写），在 frontmatter 设 `confidence: low`。
   - `/lint-wiki` 会把这些条目列为**待人工复核**。

7. **报告**：
   ```
   ## /ingest-image 报告
   来源：      <路径>
   类型：      <type>
   侧车：      <路径>.md
   实体：      E（已链接 L，新建 N）
   置信度：    high | medium | low
   ```

## 硬约束

- **绝不**修改原图文件。
- **绝不**编造图中不存在的文字。若图像不可辨识，写 `OCR: (illegible)`，并把 `confidence` 设为 `low`。
- 侧车路径由图片路径决定，**不得**散落到其他位置。
- 若图片来自受版权保护的来源（如论文 figure），且来源 frontmatter 有 `copyright: restricted`：保留侧车，但**不得**把原图搬进 `wiki/`。 wiki 页面只能通过 `[[raw/.../fig-N]]` 间接引用。
- 跳过 <10KB 或显然是装饰用途（logo、横幅、分隔线）的图片，这类图只在父 `index.md` 中保留 `alt` 文本。
