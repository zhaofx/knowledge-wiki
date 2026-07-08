---
description: 审阅 output/pending/ 下的候选，经用户批准后合并进 wiki/
---

这是内容进入 `wiki/` 前的**最后一道闸门**。未经用户逐条明确批准，不会发生任何写入。

## 步骤

1. **列举**
   - 扫描 `output/pending/*.md`，筛选 frontmatter `status: pending` 的文件。
   - 若为空，直接停止并报告：「暂无待审批候选。」

2. **审阅循环** —— 按创建时间顺序，**逐条**处理：

   a. 打印一张**紧凑的摘要卡片**：
      ```
      ── 候选 M / N ────────────────────────────
      文件：        output/pending/<slug>.md
      目标：        <target_path>
      来源 QA：     <promoted_from>
      字节数：      <size>
      摘要：        <3–5 行的蒸馏摘要>
      可能波及：    提到相同实体的现有 wiki 页面
      ──────────────────────────────────────────
      ```

   b. **询问用户**：`批准吗？[y/n/skip/edit/stop]`
      - `y`     → 合并（进入步骤 3）
      - `n`     → 拒绝（进入步骤 4）
      - `skip`  → 保留原样，处理下一条
      - `edit`  → 打印候选正文，征集修改意见后重新询问
      - `stop`  → 终止循环；未处理的候选保持 pending

3. **批准时**
   - 把文件从 `output/pending/<slug>.md` 移动到 `<target_path>`。
   - 更新已移动文件的 frontmatter：
     ```yaml
     status: merged
     approved_at: <ISO 当前时间>
     ```
   - **反向链接扫描**：对本页新引入的每个 `[[双链]]` 目标，扫描所有以**纯文本**提到同名实体的 wiki 页面，把纯文本替换为链接。
   - 重建 `wiki/index.md`。
   - 留下审计面包屑：新建 `output/pending/<slug>.md.merged`，内容为
     `merged to <target_path> at <ISO 当前时间>`。

4. **拒绝时**
   - 移动到 `output/pending/_rejected/<slug>-<timestamp>.md`。
   - 追加 frontmatter：
     ```yaml
     status: rejected
     rejected_at: <ISO 当前时间>
     rejection_reason: <向用户征集一句话原因>
     ```

5. **最终报告**：
   ```
   ## /merge-pending 报告
   批准：A
   拒绝：B
   跳过：C
   停止于：<序号或「已完成」>
   反向链接扫描更新页面数：K
   ```

## 硬约束

- 没有用户明确 `y` 之前，**不得**合并。
- **禁止**批量批准。每条候选都需要一次确认。
- **不得**静默覆盖已存在的 `<target_path>`。若已存在，切换到「合并入既有页」模式，先展示 diff 再询问。
- 全过程**不得**修改 `raw/` 下的任何文件。
