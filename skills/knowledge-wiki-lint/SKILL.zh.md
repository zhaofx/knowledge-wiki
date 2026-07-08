---
name: knowledge-wiki-lint
description: 对位于 ${KNOWLEDGE_ROOT_DIR}/knowledge 的本地数仓 LLM 知识库执行只读健康检查。触发场景包括用户说"检查知识库"、"lint wiki"、"健康检查"、"查死链"、"检查孤岛页"、"知识库有没有问题"、"检查低置信度图片"，或希望得到一份 wiki 质量问题报告。本 skill 不得修改任何文件。
---

# Knowledge Wiki Lint（知识库体检）

使用本 skill 对 wiki 执行只读健康检查。

## 工作区

```text
${KNOWLEDGE_ROOT_DIR}/knowledge
```

## 必读文件

1. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/AIDE.md`。
2. 读取 `${KNOWLEDGE_ROOT_DIR}/knowledge/aide-commands/lint-wiki.md`。

## 工作流

扫描 `wiki/` 及相关的 raw 侧车元数据，产出一份 Markdown 报告，包含：

- 死链
- 孤岛页
- 相互矛盾的陈述
- 缺失的概念 / 实体
- 综述机会
- 超长页
- 标签问题
- 低置信度图片侧车
- Top 3 推荐动作

## 远端来源入库

lint 默认为只读，不主动拉取远端材料。若某个体检结论必须借助远端来源才能判断本地 wiki/raw 是否已过期，先向用户确认再将远端原文/结果保存到 `raw/`；否则将"来源缺失 / 过期"作为一条动作项写入报告。

## 边界

- 不得修改任何文件。
- 语义类检查必须读取相关页面内容，不得只凭文件名判定。
- 若 wiki 规模较大，采用有策略的抽样并在报告中声明抽样方式。
