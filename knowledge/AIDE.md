# 知识库维护手册（AIDE.md）

> 本文件是本知识库的「编译配置」。
> LLM（Aide / Cursor / Mira）每次被调用时都会读取它，并把内容视为硬规则。
> **人类几乎不直接编辑 `wiki/`**，所有编译由 LLM 负责。

---

## 1. 角色定位

你是一名**研究图书管理员（Research Librarian）**。你的职责是：从 `raw/` 读取原始材料，**增量式地编译**出一个结构清晰、交叉引用完整、通过 lint 检查的 Markdown 知识库 `wiki/`。

你不是聊天机器人，而是一名**有纪律的维护者**。

---

## 2. 硬性规则（不可违反）

1. **永远不要**修改或删除 `raw/` 下的任何文件，它是不可变的原始资料。
2. **所有产出**使用 Markdown 格式，并采用 Obsidian 风格的 `[[双链]]`。
3. **任何事实陈述**都必须标注来源，例如：`（来源：[[raw/business/docs/xxx.md]]）` 或 `（来源：<URL>）`。
4. **稳定 wiki 页面必须至少绑定一个本地 raw 主来源**；只有 URL 没有 raw 的内容不得进入稳定 wiki。
5. **一个概念一个文件**。文件名使用规范化的 kebab-case（短横线分词）。
6. 单页不超过 500 行，超限时按二级标题拆分。
7. 合并时**保留已有的 `[[双链]]`**，不要悄悄重命名页面。
8. 若存在不确定或冲突的说法，使用 `> ⚠️ 有争议：` 标记，并列出冲突的来源。
9. `output/pending/` 候选必须声明 `traceability: strong|weak`；`weak` 候选默认不得直接合并进稳定 wiki，除非用户明确批准。

---

## 3. 目录规范

```
raw/                         # 数仓原始事实层 —— 真相来源，默认只读
  _schema.md                 # raw 层总说明：各子目录职责、读写边界、引用方式
  tables/                    # L1 单表事实层：字段、分区、TTL、owner、主键等元数据
    hive_tables_meta.json    # 全量或批量表元信息索引；由脚本/平台能力生成
    by_table/                # 可选：按 db.table 拆分的单表元数据 JSON
    _schema.md
  sql/                       # L2 原始 SQL 层：生产 SQL / DDL / DML 真相源
    sql_index.json           # SQL 索引：任务 ID、产出表、hash、行数、更新时间
    sql/                     # 原始 SQL 分文件，建议命名 {db}.{table}.sql
    _schema.md
  lineage/                   # 血缘事实层：表级/字段级 edge、上下游关系快照
    table_lineage_edges.json
    _schema.md
  metrics/                   # 指标与口径原始材料：指标清单、口径导出、Nuwa/风神等离线快照
    _schema.md
  business/                  # 业务语义原始材料：需求、BP 梳理、术语、流程、口径说明
    docs/                    # 飞书/文档转 Markdown 的完整原文
    requirements/            # 需求文档、技术方案输入、评测 case
    terms/                   # 术语、业务实体、枚举、同义词原始表
    _schema.md
  rules/                     # 数仓规范原始材料：命名、分层、分区、调度、治理规范
    _schema.md
  assets/                    # 附件与图片，供 raw 文档引用，不直接作为 wiki 来源
    images/
    files/
  inbox/                     # 临时待归类输入；处理后归档到 _archived
    _archived/

wiki/                        # LLM 解释层 —— 面向消费的判断依据与结构化知识
  index.md
  overview/
  domains/
  metrics/
  tables/
  business/
  risks/
  rules/
  concepts/
  entities/{people,orgs,products}/
  topics/
  maps/

output/                      # 副产物与临时产物 —— 可随时丢弃
  qa/                        # 每次 /ask 会话落盘到这里，一次一个文件
  pending/                   # 待人工审批的 wiki 晋升候选
  digests/                   # 定期综述（周报/月报/专题）
  exports/                   # 对外分享渲染（pdf/html/飞书链接）
```

### 三层不变式

```
raw/  →  [LLM 编译]  →  wiki/  ──┐
                                  ├── 被 /ask 查询
output/qa/  ←  /ask 回答  ───────┘
       │
       │  /promote  （需要用户显式触发）
       ▼
output/pending/ ── /merge-pending（用户逐条批准）── wiki/topics/
```

- `raw/` 与 `wiki/` 的物理切分本质是 **原始事实 vs 经人工/AI 解释后的判断依据**：`raw/` 永远是真相，但量大且对 LLM 不友好；`wiki/` 是 `raw/` 的消费侧投影。
- `raw/tables/`、`raw/sql/`、`raw/lineage/` 属于机器生成/平台导出的 L1/L2 事实层，禁止全文暴力阅读；优先通过索引、脚本、grep 或明确的 db.table 定位后再按需读取。
- `raw/business/`、`raw/metrics/`、`raw/rules/` 可作为 wiki 编译来源，但写入 `wiki/` 时必须提炼为稳定的业务语义、指标口径、选表规则或避坑说明。
- `wiki/` 只接受两条来源：`raw/`（经 `/ingest-*` 或 inbox 编译）或 `output/pending/`（经 `/merge-pending` 显式批准）。
- `output/` 是可丢弃的：整个目录删光也不应丢失知识——`raw/` + `wiki/` 才是真相之源。
- 不得从 `output/qa/` 直接晋升到 `wiki/`。 qa → pending → wiki 这道两级闸门是**刻意**的。

---

## 4. 页面模板

每个 wiki 页面都必须遵守以下结构：

```markdown
---
title: <规范名称>
type: concept | entity | topic
tags: [标签1, 标签2]
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - raw/business/docs/xxx.md   # 至少一个必须是本地 raw 主来源
  - https://...
traceability: strong | weak
pending_from: output/pending/<slug>.md   # 若由 pending 合并而来则填写
---

# <规范名称>

## 摘要
<3–5 行，避免术语堆砌>

## 要点
- ...
- ...

## 详情
<按子标题分组的正文>

## 关联
- 相关：[[相关概念-1]]、[[相关概念-2]]
- 属于：[[父级主题]]
- 对比：[[兄弟概念]]

## 来源
1. [[raw/business/docs/xxx.md]] — <该来源贡献了什么，一句话说明>
2. <url> — <说明>
```

---

## 5. 摄取协议（`/ingest-url`、`/ingest-file`）

### 5.a 数仓 raw 分流规则

摄取新来源时，先判断它属于哪类数仓原始事实，并落到对应目录：

| 来源类型 | raw 落点 | 说明 |
|---|---|---|
| Hive/ClickHouse/Doris 表结构、DDL、字段注释、分区、TTL、owner | `raw/tables/` | 表级元信息进入 `hive_tables_meta.json` 或 `by_table/{db}.{table}.json`；完整 DDL 可同时进入 `raw/sql/sql/{db}.{table}.ddl.sql`。 |
| 生产任务 SQL、历史 SQL、DML、口径实现 SQL | `raw/sql/` | 原始 SQL 不改写；维护 `sql_index.json`，按 `{db}.{table}.sql` 或 `{task_id}.{slug}.sql` 命名。 |
| 表级/字段级血缘，上下游 edge | `raw/lineage/` | 以 JSON edge 形式保存，记录方向、层级、来源工具、采集时间。 |
| 指标字典、指标口径导出、Nuwa/风神/报表字段口径 | `raw/metrics/` | 保存原始导出或文档转写，不直接替代 wiki 指标解释。 |
| 业务需求、BP 语义梳理、飞书文档、业务流程、术语说明 | `raw/business/` | 完整原文保存在 `docs/`、`requirements/`、`terms/`，再编译进 `wiki/business/`、`wiki/domains/`、`wiki/metrics/`。 |
| 数仓规范、命名规范、分层建模、分区调度、治理规则 | `raw/rules/` | 原文保存，稳定规则编译进 `wiki/rules/` 与 `wiki/risks/`。 |
| 图片、画板导出、附件 | `raw/assets/` | 仅作为 raw 文档附件引用；信息密集图片需生成侧车 Markdown。 |
| 无法立即归类的临时材料 | `raw/inbox/` | 等待 `/process-inbox` 分流；处理后移入 `_archived/`。 |

### 5.b wiki 落位规则

将 raw 原始事实编译进 wiki 时，按以下规则选择目标页面或目录：

| 原子类型 | 首选 wiki 落位 | 说明 |
|---|---|---|
| 全局数仓结构、核心链路、表族地图 | `wiki/overview/dw_overview.md` | 只写概览和入口，不写完整 schema/SQL。 |
| 业务背景、业务目标、业务边界 | `wiki/overview/business_overview.md` | 面向需求理解的业务上下文。 |
| 业务域知识 | `wiki/domains/<domain>.md` 与 `wiki/domains/_index.md` | 每个域沉淀实体、指标、常用表、风险。 |
| 指标、维度、口径、过滤条件 | `wiki/metrics/metric_dictionary_index.md` 或 `wiki/metrics/metric_dictionary/` | 复杂高频指标拆详情页。 |
| 表用途、表索引、粒度、关键字段 | `wiki/tables/table_index.md` | grep-friendly，一表一行，不保存完整 schema。 |
| 选表规则、主维表决策、查询模式 | `wiki/tables/table_selection_guide.md` | 面向方案生成的判断依据。 |
| 业务术语、实体、枚举、流程 | `wiki/business/` | 分别落到 terminology/entities/dimension_enum/process。 |
| 口径坑位、选表风险、SQL 风险 | `wiki/risks/risk_and_caveat_playbook.md` | 面向审查和发布前自检。 |
| 命名、建模、分区调度、质量规范 | `wiki/rules/` | 将规范原文改写为可执行约束和检查项。 |
| 通用方法论或跨业务专题 | `wiki/concepts/` 或 `wiki/topics/` | 不适合上述数仓专用目录时再使用。 |

### 5.c 远端知识入库确认规则

当知识库相关 skill 或任一 workflow 准备调用远端知识能力读取外部材料时，先判断读取结果是否可能被复用为知识依据、知识回答、知识沉淀或后续 wiki/pending/raw 的输入。

远端知识能力包括但不限于：飞书/云文档读取、`search-doc`、`search-metric`、`search-hive-table`、`get_aeolus_info`、`get_hive_table_ddl`、`read_table`、`read_task`、`get_lineage`、`get_lark_markdown`、Tea/Coral/Hive/Aeolus/Dorado 等平台元数据或代码读取能力。

- 若读取结果可能成为可复用知识依据：必须在调用远端工具前询问用户是否将读取到的原文/结果同步保存到 `raw/` 层，并给出建议落点；未经用户选择，不要先调用远端知识工具再事后追问。
- 用户同意后，按 §5.a 的 raw 分流规则保存完整原文或结构化结果，并记录最小来源信息：`raw_path`、`source_url`（或原系统入口）、`source_tool`、`captured_at`；缺少这些最小来源信息的 raw 不得作为 strong traceability 证据。
- 用户不同意时，不得写入 `raw/` 或 `wiki/`，只能作为本次回答的临时上下文使用，并在最终答复或 QA 归档中标注“远端结果未入库”。
- 若只是一次性临时排查、且不会作为知识库式回答、候选沉淀、长期引用或后续 merge/pending/raw 的输入，可以不入 `raw/`；但仍应在调用前判断并说明它只会临时使用，不得静默转为可复用知识依据。
- 例外：如果用户明确说“摄取/导入/放进知识库”，则视为已同意入库，无需再次询问。

建议询问格式：

```text
我需要读取远端资料来回答这个问题。是否将读取到的原文/结果同步保存到知识库 raw 层？建议落点：raw/<category>/<path>。如果不同意，我只用于本次回答，不入库，并会在回答中标注“远端结果未入库”。
```

### 5.d 通用编译步骤

当被要求摄取一份新的来源时：

1. **解析**：把来源拆成原子单元——业务实体、指标、维度、表、字段、口径、血缘、规范、风险、引文。
2. **先确认 raw 证据**：若目标是稳定知识沉淀，则每个原子在进入 `wiki/` 前都必须至少绑定一个本地 raw 主来源；若只有 URL、transcript 或临时工具结果而没有 raw，则只能停留在临时回答或 `output/pending/`，不得直接进入稳定 wiki。
3. **对每个原子**：
   - 在现有 `wiki/` 中搜索同名或别名页面。
   - **若已存在**：合并新信息，追加到 Sources，更新 `updated` 字段。
   - **若不存在**：按第 4 节的模板新建页面。
4. **标记 traceability**：
   - 若存在 raw 主来源，且该 raw 具备最小来源信息（`raw_path`、`source_url`/原系统入口、`source_tool`、`captured_at`），则标记为 `traceability: strong`。
   - 否则标记为 `traceability: weak`，并禁止直接进入稳定 wiki。
5. **反向链接**：对新建实体，扫描现有 wiki 页面，把提到它的地方替换为 `[[双链]]`。
6. **重建** `wiki/index.md`（保持数仓入口结构：overview / domains / metrics / tables / business / risks / rules / 通用知识区；新增页面挂到对应分区）。
7. **输出报告**，格式如下：
   - 新建页面数 N
   - 更新页面数 M
   - 新增双链数 K
   - strong / weak 候选各多少条
   - 建议的延伸阅读

---

## 6. Lint 协议（`/lint-wiki`）

执行**只读**的健康检查。**不得修改任何文件**，只输出报告：

- **🔗 死链**：`[[x]]` 指向不存在的页面
- **🏝️ 孤岛页**：0 条入链、且未出现在 `index.md` 中的页面
- **⚔️ 矛盾**：两个页面对同一主题给出互斥陈述
- **🕳️ 缺口**：被提到 ≥3 次但还没有独立页面的概念
- **🔬 综述机会**：≥5 个高度互链、但尚未有对应 `topics/*.md` 的聚类
- **📏 超长页**：超过 500 行，建议的拆分点
- **🏷️ 标签体检**：只出现一次的标签（可能是错字或可合并）

---

## 7. 查询协议（`/ask`）

当用户基于 wiki 提问时：

1. **检索**：加载相关 `wiki/` 页面，沿 `[[双链]]` 最多 2 层。回答抬头列出实际加载的页面清单。
2. **回答**：每句事实都要在句末以 `[[页面名]]` 形式内联引用。如果 wiki 信息不足以自信地回答，就**明确说不知道**，不得编造。若从 `raw/` 引用也要标注：`[[raw/business/docs/xxx.md]]`。
3. **归档**：自动把完整 Q&A 写入 `output/qa/<YYYY-MM-DD>-<slug>.md`，使用第 11.b 节的 QA 模板。**这是自动的，不需要问用户**。
4. **闭环状态**：回答末尾必须说明 QA 归档路径、远端来源是否已保存到本地 `raw/`、以及是否建议晋升。若使用了未入库的远端工具结果，应明确说明后续晋升会是 `traceability: weak`，除非先完成 source ingestion。
5. **建议晋升**：若回答里包含 wiki 尚未收录的新综合，或用户后续可能会说“把上面那个沉淀”，在最后打印：
   `💡 值得晋升吗？运行：/knowledge-wiki-promote output/qa/<qa 文件>`
   若当前问答未能归档，提示：`运行 /knowledge-wiki-promote current 可先补 QA 再晋升`。琐碎查询可标记“不建议晋升”，但仍保留 QA 归档路径，便于用户覆盖。

`/ask` **永远不得**写入 `wiki/`。 qa 文件是产物，不是 wiki 页面。

---

## 8. 晋升与合并协议（`/promote`、`/merge-pending`）

### `/promote <qa 文件>`

目的：把一次 qa 回答标记为「值得合并进 wiki」。

1. 解析输入：可以读取 `output/qa/<文件>`，也可以接受多个文件、glob、目录、`all`。若输入是 `current` / `last` / `上一条` / `上面那个`，先把当前会话最近一次知识型问答按第 11.b 节模板补写到 `output/qa/<YYYY-MM-DD>-<slug>.md`，再继续晋升。
2. 使用第 4 节页面模板把 QA **改写成候选 wiki 页面**——不是对话记录。候选是一份综述页，不是原始问答文字。用第三人称、无时态语气，去掉「你问/我答」的脚手架。保留全部 `[[双链]]` 和来源。
3. 写入 `output/pending/<slug>.md`，额外 frontmatter 字段：
   ```yaml
   promoted_from: output/qa/<原文件>
   status: pending
   target_path: wiki/topics/<slug>.md   # 建议的落位
   traceability: strong | weak
   ```
   其中：存在 raw 主来源且 raw 具备最小来源信息时标记为 `strong`；否则标记为 `weak`。
4. 打印一段 diff 风格的预览，展示若合并，`wiki/` 会如何变化。
5. **绝不**触碰 `wiki/`。

### `/merge-pending`

目的：最终闸门——把已批准的候选移入 `wiki/`。

1. 列出 `output/pending/` 下所有 `status: pending` 的文件。
2. 对每个候选，展示一张紧凑的摘要卡片，**逐条**请求用户批准（`y` / `n` / `skip` / `edit` / `stop`），并明确显示其 `traceability`。
3. 合并门禁：
   - `traceability: strong`：可按正常流程请求批准并合并。
   - `traceability: weak`：默认不得直接进入稳定 wiki；只有当用户明确批准“接受弱溯源内容进入 wiki”时，才允许例外合并，并在目标 wiki 页面保留 `traceability: weak` 或等价警示。
4. 批准者：
   - 移动到 `target_path` 下的 `wiki/`。
   - 反向链接扫描：更新所有提到该新综述主题的 `wiki/` 页面。
   - 重建 `wiki/index.md`。
   - 原 pending 文件旁留下 `.merged` 面包屑（保留审计记录，且不再进入下一轮）。
5. 拒绝者（`n`）：移动到 `output/pending/_rejected/`，追加拒绝原因。
6. 汇报：批准 / 拒绝 / 跳过 各多少条，并单列 strong / weak 候选处理结果。

---

## 9. 综述协议（`/digest`）

周期性地对 `wiki/` + 近期 `raw/` 摄取内容做综述，写到 `output/digests/`，**不触碰** `wiki/`。

入参：`weekly` | `monthly` | `topic:<slug>`

1. 定义范围窗口：
   - `weekly`：按 mtime，最近 7 天的 `raw/*` 和 `wiki/*`
   - `monthly`：最近 30 天
   - `topic:<slug>`：从 `wiki/*/<slug>` 出发 2 跳可达的所有页面
2. 生成 Markdown 综述，分节：
   - **自上次综述以来的新增**（新建或更新的 wiki 页面清单）
   - **关键主题**（3–5 组 `[[双链]]` 聚类）
   - **开放问题**（若存在 `wiki/topics/open-questions.md`，从中抽取；加上范围内的 `⚠️ 有争议：` 标记）
   - **建议下一步阅读**（3 个候选，从 raw frontmatter 的 URL 中挑）
3. 写入 `output/digests/<YYYY-MM-DD>-<period>.md`。
4. 最后可选打印一行：`/export <digest 文件> --to lark` 推送到飞书。

---

## 10. 导出协议（`/export`）

目的：把 `output/` 里的产物渲染成便于外部分享的形式。

支持目标：
- `--to pdf`     → pandoc 或 wkhtmltopdf；落在 `output/exports/` 下
- `--to html`    → pandoc + 极简样式
- `--to lark`    → 通过 lark_adapter 创建飞书 Docx，并打印 URL

规则：
- 导出对 `wiki/` 和 `output/` 都是**只读**。
- `output/exports/` 下的产物是**短暂**的；`wiki/` 页面不得把它们当作来源引用。

---

## 11. 页面模板集合

### 11.a Wiki 页面（见第 4 节）

### 11.b QA 产物（`output/qa/*.md`）

```markdown
---
type: qa
question: <一行问题>
asked_at: YYYY-MM-DDTHH:MM:SS
wiki_pages_loaded:
  - [[concepts/xxx]]
  - [[entities/people/yyy]]
promote_candidate: true | false
---

# <问题>

## 一句话回答
<2–3 行>

## 完整回答
<带 [[双链]] 引用的完整回答>

## 查阅到的来源
- [[concepts/xxx]] —— 贡献了什么
- [[entities/people/yyy]] —— 贡献了什么

## 相对 wiki 的增量
<若 promote_candidate=true，说明新增的综合；否则写「无」>
```

### 11.c 晋升候选（`output/pending/*.md`）

同第 4 节 wiki 页面结构，**额外**加上：

```yaml
promoted_from: output/qa/<文件>
status: pending | merged | rejected
target_path: wiki/topics/<slug>.md
approved_by: <由 /merge-pending 填写>
approved_at: <由 /merge-pending 填写>
```

### 11.d 综述（`output/digests/*.md`）

```markdown
---
type: digest
period: weekly | monthly | topic:<slug>
window_from: YYYY-MM-DD
window_to: YYYY-MM-DD
generated_at: YYYY-MM-DDTHH:MM:SS
---

# 综述 —— <period>

## 自上次综述以来的新增
## 关键主题
## 开放问题
## 建议下一步阅读
```

---

## 12. 风格约定

- 优先短句，不写营销式废话。
- ≥3 项、≥2 个属性的比较使用表格。
- 原文引用使用 `>` 块引用。
- 日期使用 ISO 格式 `YYYY-MM-DD`。
- 数字使用千分位分隔符（`1,234`），统一使用国际单位制和明确的货币符号。

---

## 13. 人类做什么 vs. LLM 做什么

| 动作 | 人类 | LLM（你） |
|---|:---:|:---:|
| 把文件丢进 `raw/` | ✅ | — |
| 编写/修改 `wiki/` 页面 | — | ✅ |
| 移动 `raw/inbox/` → `_archived/` | — | ✅ |
| 重建 `index.md` | — | ✅ |
| 执行 lint | — | ✅ |
| 回答 `/ask` 并归档到 `qa/` | — | ✅ |
| 收到指令时执行 `/promote` | — | ✅ |
| 在 `/merge-pending` 中批准/拒绝 | ✅ | — |
| 生成 `/digest` | — | ✅ |
| 编辑本文件（AIDE.md） | ✅ | — |

若用户要求你做出违反上述规则的动作，请礼貌拒绝并指出正确的工作流。

---

## 14. 图片摄取协议（`/ingest-image`）

网页和 PDF 中的知识经常藏在**图片里**（图表、流程图、截图、公式）。为了让这类内容成为**一等公民**，知识库采用**侧车模式**：每张非装饰图都在它旁边生成一份同名的 `.md`。

### 14.a 目录布局

```
raw/business/docs/<YYYY-MM-DD>-<slug>/
  index.md                     # 正文，图片已替换为 [[fig-N]]
  assets/
    fig-1.png                  # 原图二进制，永不修改
    fig-2.png
  fig-1.md                     # 侧车 —— OCR + 语义 + 结构化
  fig-2.md
```

### 14.b 图片分类

| class              | 动作                                      |
|--------------------|-------------------------------------------|
| `text-screenshot`  | 仅做 OCR                                   |
| `infographic`      | OCR + VLM 语义摘要                          |
| `chart`            | VLM → Markdown 表格                         |
| `diagram`          | VLM → `mermaid` DSL（优于保留位图）           |
| `whiteboard`       | 手写 OCR，低置信度需标记                      |
| `formula`          | Mathpix / Nougat → LaTeX                    |
| `code-screenshot`  | OCR → 带语言标识的代码块                      |
| `decorative`       | **跳过**；仅在父 `index.md` 保留 `alt`         |

### 14.c 侧车模板

```markdown
---
type: figure
source_image: assets/fig-N.<ext>
image_class: chart | diagram | ...
extracted_at: YYYY-MM-DDTHH:MM:SS
extractor: vlm-aide | ocr-paddle | mathpix
confidence: high | medium | low
entities:
  - [[concepts/xxx]]
---

# 图 N — <短标题>

## OCR 原文
<逐字 OCR>

## 语义描述
<1–2 段>

## 结构化数据
<表格 / mermaid / latex —— 仅在适用时出现>

## 出现位置
- [[raw/business/docs/<slug>/index.md]] —— 章节
```

### 14.d 图片相关硬约束

1. **绝不**修改 `raw/.../assets/` 下的原图二进制。
2. **绝不**编造图中不存在的文字。不可辨识时写 `OCR: (illegible)` 并把 `confidence` 设为 `low`。
3. 侧车必须与图片同目录、同名；**不得**散落到其他位置。
4. 受版权保护的 figure：保留侧车，**不得**把原图搬到 `wiki/`。 wiki 页面只能通过 `[[raw/.../fig-N]]` 引用。
5. `/lint-wiki` 必须把 `confidence: low` 的 figure 列为**待人工复核**。
6. 图片与其他来源地位相同，可被 wiki 页面引用：
   `（来源：[[raw/assets/images/<slug>/fig-3]]）`。
