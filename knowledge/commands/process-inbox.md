---
description: 处理 raw/inbox/ 中的所有条目，并整合进 wiki/
---

你将清空 inbox —— 把每条临时笔记整合进知识库。

## 步骤

1. **列出** `raw/inbox/` 下的所有文件（跳过 `_archived/` 子目录）。

2. 对每个文件，依次执行：

   a. **分类**为以下之一：
      - `concept`（概念）→ 候选进入 `wiki/concepts/`
      - `entity`（实体）→ 候选进入 `wiki/entities/{people,orgs,products}/`
      - `quote`（引文）→ 嵌入到某个已有页面
      - `idea`（观点）→ 个人观察，并入相关 topic 页
      - `question`（问题）→ 开放性问题，追加到 `wiki/topics/open-questions.md`

   b. **整合**（遵循 AIDE.md 第 5 节「摄取协议」）：
      - 找到匹配的 wiki 页则合并；否则按第 4 节模板新建。
      - 始终以如下方式引用 inbox 原件：
        `（来源：[[raw/inbox/_archived/<文件名>]]）`

   c. **归档**：把处理过的文件从 `raw/inbox/` 移动到 `raw/inbox/_archived/`
      （保留文件名；若无日期前缀则补加日期）。

3. **重建** `wiki/index.md`。

4. **输出报告**：

   ```
   ## Inbox 处理报告

   已处理：N 条
   - <文件名> → 分类为 <类型> → [[目标页]]（新建|更新）
   - ...

   新建页面数：X
   更新页面数：Y
   跳过条目（含原因）：Z
   ```

## 硬约束

- 若某条笔记语义模糊或缺少上下文，**不得强行猜测**——保留在 inbox，并在「跳过条目」中写明原因。
- 若两条 inbox 内容冲突，两者都整合进去，并在目标页用 `> ⚠️ 有争议：` 标记。
- 归档对 LLM 而言是不可逆操作——当 inbox 条目总数 > 20 时，**必须先向用户确认**再归档。
