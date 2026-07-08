# knowledge-wiki

数据仓库领域：面向 AI 的知识编译、管理与消费。

本仓库是一个**面向数据仓库领域特化的 LLM Wiki**，落地 Andrej Karpathy 提出的 **LLM Wiki** 知识管理范式：人类只投喂原始材料，LLM 负责编译、维护、查询、综述整个知识库。

> **本仓库是纯骨架** —— 只带目录、[AIDE.md](file:///Users/bytedance/git/knowledge-wiki/knowledge/AIDE.md)、[aide-commands/](file:///Users/bytedance/git/knowledge-wiki/knowledge/aide-commands)、[skills/](file:///Users/bytedance/git/knowledge-wiki/skills)，**不携带任何示例的 wiki 页面或 raw 素材**。`knowledge/wiki/**`、`knowledge/raw/**`、`knowledge/output/**` 下的实际内容都被 `.gitignore` 忽略；用户本地 ingest 出的知识仅存在于本机，不会误提交回骨架仓库。

> "Obsidian 是 IDE，LLM 是程序员，wiki 是代码库，`raw/` 是源代码。"

## 它是什么？

一个仓库、两层执行界面、一份编译配置：

1. **编译配置** —— [knowledge/AIDE.md](file:///Users/bytedance/git/knowledge-wiki/knowledge/AIDE.md)：把任意长上下文 LLM 变成**有纪律的数仓知识库维护者**。定义了目录规范、页面模板、摄取协议、`traceability: strong|weak` 溯源约束、远端知识入库确认规则等硬性规则。
2. **底层命令模板** —— [knowledge/aide-commands/](file:///Users/bytedance/git/knowledge-wiki/knowledge/aide-commands)：8 份可复用的执行手册（`ask.md` / `ingest-url.md` / `ingest-image.md` / `process-inbox.md` / `lint-wiki.md` / `promote.md` / `merge-pending.md` / `digest.md`）。所有 Skill 都会先读 AIDE.md，再按对应模板执行；不加载 Skill 的宿主（如原生 Aide）也能直接引用这些模板。
3. **上层 Skill 封装** —— [skills/](file:///Users/bytedance/git/knowledge-wiki/skills)：7 个 Skill，是 `aide-commands/` 的 Skill 化包装，覆盖「摄取 → 查询 → 晋升 → 综述」的完整闭环。任何加载 Skill 的 Agent 宿主（Trae / Claude Code / Cursor / Mira 等）都能以自然语言触发同一套工作流：

   | 阶段 | Skill | 用户可能说的话 | 对应命令模板 |
   |---|---|---|---|
   | 摄取 | [knowledge-wiki-ingest](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-ingest) | "摄取进知识库"、"把这个文档导入知识库" | `ingest-url.md` / `ingest-image.md` |
   | 清理 | [knowledge-wiki-inbox](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-inbox) | "处理 inbox"、"清理待归类" | `process-inbox.md` |
   | 体检 | [knowledge-wiki-lint](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-lint) | "lint 知识库"、"检查 wiki 有没有问题" | `lint-wiki.md` |
   | 查询 | [knowledge-wiki-ask](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-ask) | "问我的知识库"、"这个指标怎么算" | `ask.md` |
   | 晋升 | [knowledge-wiki-promote](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-promote) | "把上面那个沉淀"、"晋升刚才的回答" | `promote.md` |
   | 合并 | [knowledge-wiki-merge](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-merge) | "合并 pending"、"批准候选" | `merge-pending.md` |
   | 综述 | [knowledge-wiki-digest](file:///Users/bytedance/git/knowledge-wiki/skills/knowledge-wiki-digest) | "生成本周 digest"、"做个专题综述" | `digest.md` |

   每个 Skill 目录同时包含 `SKILL.md`（英文，Agent 默认加载）与 `SKILL.zh.md`（中文只读副本，供人工阅读 / 二次修改）。

   对于 Trae 宿主，[scripts/bootstrap.sh](file:///Users/bytedance/git/knowledge-wiki/scripts/bootstrap.sh) 会把 `skills/*/SKILL.md` 幂等同步到 `.trae/skills/` —— Trae 自动从这个目录加载 Skill；`.trae/` 已在 `.gitignore` 中忽略，不入 git。

---

## 目录结构

```
knowledge-wiki/
├── README.md                       # 当前文件
├── .env                            # 本机变量（含 KNOWLEDGE_ROOT_DIR），不入 git
├── .env.example                    # 环境变量模板
├── .gitignore                      # 忽略 .env / .trae / .obsidian / knowledge 下用户内容
├── scripts/
│   └── bootstrap.sh                # 一键初始化：目录 + wiki/index.md 种子 + .env + Skill 同步
├── skills/                         # 7 个 Skill 定义（版本化源）
│   ├── knowledge-wiki-ingest/      # 每个目录含 SKILL.md（EN）与 SKILL.zh.md（ZH）
│   ├── knowledge-wiki-inbox/
│   ├── knowledge-wiki-lint/
│   ├── knowledge-wiki-ask/
│   ├── knowledge-wiki-promote/
│   ├── knowledge-wiki-merge/
│   └── knowledge-wiki-digest/
├── .trae/skills/                   # Trae 运行时缓存（bootstrap.sh 自动同步；不入 git）
└── knowledge/                      # 实际工作目录（.keep 骨架入 git；.md 内容不入 git）
    ├── AIDE.md                     # LLM 维护者的硬规则（数仓特化版）
    ├── aide-commands/              # 命令模板（Skill 与原生 Aide 共用的执行手册）
    │   ├── ask.md
    │   ├── ingest-url.md
    │   ├── ingest-image.md
    │   ├── process-inbox.md
    │   ├── lint-wiki.md
    │   ├── promote.md
    │   ├── merge-pending.md
    │   └── digest.md
    ├── raw/                        # 数仓原始事实层 —— 人类添加，LLM 只读
    │   ├── tables/                 # L1 单表事实层：字段、分区、TTL、owner、DDL
    │   ├── sql/                    # L2 原始 SQL 层：生产 SQL / DDL / DML
    │   ├── lineage/                # 表级 / 字段级血缘 edge
    │   ├── metrics/                # 指标字典、口径导出
    │   ├── business/               # 业务需求、术语、流程、飞书文档转 Markdown
    │   ├── rules/                  # 数仓命名、分层、分区、调度、治理规范原文
    │   ├── assets/                 # 附件与图片（供 raw 文档引用）
    │   └── inbox/                  # 临时待归类输入
    │       └── _archived/
    ├── wiki/                       # LLM 解释层 —— 面向消费的判断依据
    │   ├── index.md                # 中性骨架种子（入 git）；其余 wiki 页面不入 git
    │   ├── overview/               # 数仓 / 业务全局概览
    │   ├── domains/                # 业务域知识
    │   ├── metrics/                # 指标口径与计算逻辑
    │   ├── tables/                 # 表索引、选表规则、选表决策树
    │   ├── business/               # 业务术语、实体、枚举、流程
    │   ├── risks/                  # 避坑手册、口径风险、SQL 风险
    │   ├── rules/                  # 数仓规范的可执行约束层
    │   ├── concepts/               # 通用范式的概念页（可选）
    │   ├── topics/                 # 跨领域专题
    │   ├── maps/                   # 概览图 / 地图
    │   └── entities/               # 保留自通用范式，本项目暂未使用
    │       ├── people/
    │       ├── orgs/
    │       └── products/
    └── output/                     # 可丢弃的副产物 —— 不是真相之源（内容不入 git）
        ├── qa/                     # 每次问答都会归档到这里
        ├── pending/                # 待人工批准的晋升候选（含 _rejected/）
        ├── digests/                # 周 / 月 / 专题综述
        ├── exports/                # 对外渲染
        └── raw_capture_sessions/   # 摄取远端来源时的原始抓取会话记录
```

`knowledge/raw/` 与 `knowledge/wiki/` 的物理切分本质是 **原始事实 vs 经 LLM 解释后的判断依据**：`raw/` 永远是真相；`wiki/` 是它面向消费的投影。

---

## raw 分流规则

添加原始材料时，按下表放入对应目录；无法立即归类的材料先放到 `raw/inbox/`，交给 `knowledge-wiki-inbox` 处理：

| 来源类型 | raw 落点 | 说明 |
|---|---|---|
| 表结构、DDL、字段注释、分区、TTL、owner | `raw/tables/` | 单表事实层，适合平台 / MCP / 脚本生成。 |
| 生产任务 SQL、历史 SQL、DML、口径实现 SQL | `raw/sql/` | 原始 SQL 不改写；若需批量索引可自行维护 `sql_index.json`。 |
| 表级 / 字段级血缘、上下游 edge | `raw/lineage/` | 以 JSON edge 保存，记录方向、层级、来源工具、采集时间。 |
| 指标字典、口径导出 | `raw/metrics/` | 保存原始口径材料，再编译进 `wiki/metrics/`。 |
| 业务需求、语义梳理、业务流程、术语说明 | `raw/business/` | 保存完整原文，再编译进 `wiki/business/` / `wiki/domains/`。 |
| 命名、分层、分区、调度、治理规范 | `raw/rules/` | 保存规范原文，稳定内容编译进 `wiki/rules/` 与 `wiki/risks/`。 |
| 图片、画板导出、附件 | `raw/assets/` | 信息密集图片需生成侧车 Markdown。 |
| 无法立即归类的材料 | `raw/inbox/` | 等待处理和分流。 |

> `raw/tables/`、`raw/sql/`、`raw/lineage/` 体量可能很大，默认按索引或 `db.table` 精确读取，**禁止全文灌入**。

---

## 快速开始

1. **克隆仓库**。

2. **一键初始化**：

   ```bash
   bash scripts/bootstrap.sh
   ```

   该脚本会做四件事，全部幂等（重复运行安全）：
   - 补齐 `knowledge/{raw,wiki,output}/` 三层目录骨架 + `.keep` 占位；
   - 若 `knowledge/wiki/index.md` 缺失，写入中性骨架种子；
   - 若 `.env` 缺失，从 `.env.example` 复制一份；
   - 把 `skills/*/SKILL.md` 幂等同步到 `.trae/skills/`（Trae 自动加载路径）。

3. **配置本机变量**：编辑 `.env`，把 `KNOWLEDGE_ROOT_DIR` 填成本机的仓库绝对路径。所有 Skill 都以 `${KNOWLEDGE_ROOT_DIR}/knowledge/...` 定位工作区，`.env` 本身不入 git。

   ```bash
   # .env
   KNOWLEDGE_ROOT_DIR=/absolute/path/to/knowledge-wiki
   ```

4. **让 Agent 宿主加载 Skill**：
   - **Trae**：无需额外操作，`bootstrap.sh` 已把 Skill 同步到 `.trae/skills/`，Trae 启动时自动装载。
   - **其他宿主**（Claude Code / Cursor / Mira 等）：把 [skills/](file:///Users/bytedance/git/knowledge-wiki/skills) 下的 7 个 Skill 装载到宿主。宿主会自动通过 SKILL 的 `description` 匹配用户意图，进入对应 Skill 后读取 [AIDE.md](file:///Users/bytedance/git/knowledge-wiki/knowledge/AIDE.md) 与对应命令模板作为硬规则。

5. **摄取一份材料**（表元数据、SQL、业务文档、URL、飞书文档、图片……）：

   > "把这份飞书文档摄取进知识库"

   Agent 会加载 `knowledge-wiki-ingest`，按 `raw/` 分流规则保存原文，然后编译进 `wiki/` 对应分区。

6. **每周巡检**：

   > "处理 inbox"
   > "lint 一下 wiki"
   > "生成本周 digest"

**绝不手改 `wiki/`** —— 如果某页有问题，告诉 LLM 哪里不对，让它自己修。

### 不加载 Skill 的宿主（例如原生 Aide）

命令模板 `knowledge/aide-commands/*.md` 可以直接被引用。用一句话把 AIDE.md + 对应模板告诉宿主即可：

```text
请在 ${KNOWLEDGE_ROOT_DIR}/knowledge 下，读取 AIDE.md，并按 aide-commands/ask.md 执行：这个指标应该选哪张表？
```

或：

```text
请在 ${KNOWLEDGE_ROOT_DIR}/knowledge 下，按 aide-commands/process-inbox.md 处理 inbox。
```

---

## 查询与晋升路径

wiki 只是系统的一半，另一半是**使用 wiki** 时会发生什么：

```
[提问]  "X 指标怎么算？"
  → knowledge-wiki-ask：加载 wiki/，用 [[双链]] 内联引用作答
  → 归档到 output/qa/<YYYY-MM-DD>-<slug>.md
  → 提示："💡 值得晋升吗？"

[晋升]  "把上面那个沉淀"
  → knowledge-wiki-promote：把 QA 改写为一篇正式 wiki 页面（第三人称、无时态）
  → 生成候选 output/pending/<slug>.md，标记 traceability: strong|weak
  → **不触碰** wiki/

[合并]  "合并 pending"
  → knowledge-wiki-merge：先按"建议合并 / 建议编辑 / 建议跳过 / 建议拒绝"分组总览
  → 再逐条展示候选，请求 y/n/skip/edit/stop
  → 「y」：合并到 wiki/，更新反向链接与 index
  → 「n」：移到 output/pending/_rejected/
  → 默认拒绝 weak 溯源候选，除非用户显式批准

[综述]  "生成本周 digest"
  → knowledge-wiki-digest：综述最近 7 天 wiki/ + raw/ 的变化
  → 写入 output/digests/
```

`qa → pending → wiki` 是**刻意**的两级人工闸门：`ask` 永远不得直接写 wiki；候选也必须逐条经用户批准才落地。

`output/` 是**可丢弃的**。整个目录删光也不会丢失知识——`raw/` + `wiki/` 才是唯一的真相之源。

---

## 数仓特化的溯源约束

相较通用 LLM Wiki 范式，本项目在 [AIDE.md](file:///Users/bytedance/git/knowledge-wiki/knowledge/AIDE.md) 中新增了两条数仓专用约束：

1. **`traceability: strong|weak`** —— 每个 pending 候选必须声明溯源强度。只有本地 raw 主来源（且具备 `raw_path` / `source_url` / `source_tool` / `captured_at` 最小来源信息）的内容才是 `strong`，才允许直接合并进稳定 wiki。
2. **远端知识入库确认规则** —— 调用 `search-metric`、`get_hive_table_ddl`、`read_table`、`get_lark_markdown` 等远端知识能力前，必须先询问用户是否将读取到的原文同步保存到 `raw/`；未入库的远端结果不得作为 strong 溯源证据，落地后统一放到 `output/raw_capture_sessions/` 与对应 `raw/<category>/` 下。

---

## 不适合的场景

- 合规内容（法律、医疗、金融建议）—— LLM Wiki 范式没有逐条论断的审计轨迹。
- 对外客户文档 —— 没有人工同行评审。
- 高频变更的团队 wiki —— 人类每次手改都可能被下一轮 LLM 重编译覆盖。可行做法是**只给一个服务账号写权限**。

---

## 维护原则

- 不手改 `wiki/`。由 LLM 按 [AIDE.md](file:///Users/bytedance/git/knowledge-wiki/knowledge/AIDE.md) 规则维护；发现问题就告诉它哪里不对，让它自己重编译。
- `raw/tables/`、`raw/sql/`、`raw/lineage/` 体量可能很大，默认按索引或 `db.table` 精确读取，禁止全文灌入。
- 所有事实陈述都要引用来源（本地 `raw/` 路径或外部 URL）。
- 有争议 / 不确定的信息要显式标注。
- `knowledge-wiki-merge`（对应 `aide-commands/merge-pending.md`）是内容进入正式 `wiki/` 的最终人工闸门；不接受批量合并。

---

## 致谢

灵感来自 [Andrej Karpathy 的 `llm-wiki.md` Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 以及他在 X 上发表的 [LLM Knowledge Bases 帖子](https://x.com/karpathy/status/2039805659525644595)。raw 层的 L0 / L1 / L2 分层与 raw / wiki 物理切分参考了字节内部飞书文档 [《语义开发 Skill 探索及轻量化 Wiki 生成实践》](https://bytedance.larkoffice.com/wiki/XDpgwgmOOiFVtAkKuNvcbxUmnwf)。
