---
name: knowledge-wiki-digest
description: 为位于 ${KNOWLEDGE_ROOT_DIR}/knowledge 的本地数仓 LLM 知识库生成周报 / 月报 / 专题综述。触发场景包括用户说"生成知识库周报/月报"、"digest"、"知识库综述"、"总结最近知识库变化"、"这个 topic 做个综述"，或要求做某段时间 / 某个专题的汇总。产物只写入 output/digests/。
---

# Knowledge Wiki Digest（知识库综述）

使用本 skill 生成综述产物。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/commands/digest.md`。

## 入参

- 默认 `weekly`
- `monthly`
- `topic:<slug>`

## 工作流

1. 确定时间窗口或专题范围。
2. 读取相关 `wiki/` 页面和近期 `raw/` 来源。
3. 写入一个综述文件到 `output/digests/<YYYY-MM-DD>-<period>.md`。
4. 综述应包含：
   - 新建 / 更新的页面
   - 关键主题
   - 开放问题
   - 建议的下一步阅读
5. 打印综述文件路径。

## 远端来源入库

综述以本地 `wiki/` 和 `raw/` 为主要素材。若判断必须借助远端来源来解释某项变化或填补空白，先向用户确认再将远端原文/结果保存到 `raw/`。用户拒绝时，只使用本地内容，或明确标注该远端材料"未入库"。

## 边界

- 不得写入 `wiki/`。
- 不得自动推送到飞书。
- 即便本次窗口无变更，也要写出一份"无实质变化"的综述以保持节奏一致性。
