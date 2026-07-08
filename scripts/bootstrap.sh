#!/usr/bin/env bash
# ==============================================================================
# knowledge-wiki 一次性初始化脚本
# ------------------------------------------------------------------------------
# 定位：
#   本仓库是纯骨架 —— 只带目录、AIDE.md、commands、skills；
#   不携带任何示例的 wiki 页面或 raw 素材。用户 clone 之后跑此脚本，
#   会得到一个空的、准备好摄取（ingest）的知识库工作区。
#
# 作用：
#   1. 在 knowledge/ 下创建 raw/、wiki/、output/ 三层数仓特化目录骨架
#   2. 用 .keep 文件让 git 跟踪空目录（避免 clone/zip 丢失目录）
#   3. 若 wiki/index.md 缺失，写入面向数仓的入口索引种子（仅骨架分节，无条目）
#   4. 若 .env 缺失，从 .env.example 复制一份并提示填写 KNOWLEDGE_ROOT_DIR
#   5. 同步 skills/ → .trae/skills/ 作为 Trae 运行时加载入口
#
# 注意：
#   - 此脚本不会写入任何示例业务内容；所有 knowledge/wiki/**、knowledge/raw/**、
#     knowledge/output/** 下的实际内容都被 .gitignore 忽略，用户本地 ingest 出的
#     文件仅存在于本机，不会误提交到骨架仓库。
#
# 使用：
#   bash scripts/bootstrap.sh
# ==============================================================================
set -euo pipefail

# 切到仓库根目录（scripts/ 的父目录）
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

echo "→ 初始化 knowledge-wiki (root: ${REPO_ROOT})"
echo ""

# ------------------------------------------------------------------------------
# 1. 目录骨架 —— 与 knowledge/AIDE.md §3 目录规范保持一致
# ------------------------------------------------------------------------------

# raw/ 数仓原始事实层（人类写入，LLM 只读）
mkdir -p knowledge/raw/tables
mkdir -p knowledge/raw/sql
mkdir -p knowledge/raw/lineage
mkdir -p knowledge/raw/metrics
mkdir -p knowledge/raw/business/{docs,requirements,terms}
mkdir -p knowledge/raw/rules
mkdir -p knowledge/raw/assets/{images,files}
mkdir -p knowledge/raw/inbox/_archived

# wiki/ LLM 解释层（LLM 写入，人类阅读）
mkdir -p knowledge/wiki/{overview,domains,metrics,tables,business,risks,rules}
mkdir -p knowledge/wiki/{concepts,topics,maps}
mkdir -p knowledge/wiki/entities/{people,orgs,products}

# output/ 副产物（可丢弃）
mkdir -p knowledge/output/{qa,pending,digests,exports,raw_capture_sessions}
mkdir -p knowledge/output/pending/_rejected

# ------------------------------------------------------------------------------
# 2. .keep 占位 —— 让 git 跟踪空目录
# ------------------------------------------------------------------------------
KEEP_DIRS=(
  # raw
  knowledge/raw/tables
  knowledge/raw/sql
  knowledge/raw/lineage
  knowledge/raw/metrics
  knowledge/raw/business
  knowledge/raw/business/docs
  knowledge/raw/business/requirements
  knowledge/raw/business/terms
  knowledge/raw/rules
  knowledge/raw/assets
  knowledge/raw/assets/images
  knowledge/raw/assets/files
  knowledge/raw/inbox
  knowledge/raw/inbox/_archived
  # wiki
  knowledge/wiki/overview
  knowledge/wiki/domains
  knowledge/wiki/metrics
  knowledge/wiki/tables
  knowledge/wiki/business
  knowledge/wiki/risks
  knowledge/wiki/rules
  knowledge/wiki/concepts
  knowledge/wiki/topics
  knowledge/wiki/maps
  knowledge/wiki/entities/people
  knowledge/wiki/entities/orgs
  knowledge/wiki/entities/products
  # output
  knowledge/output/qa
  knowledge/output/pending
  knowledge/output/pending/_rejected
  knowledge/output/digests
  knowledge/output/exports
  knowledge/output/raw_capture_sessions
)

for d in "${KEEP_DIRS[@]}"; do
  [[ -f "$d/.keep" ]] || : > "$d/.keep"
done

# ------------------------------------------------------------------------------
# 3. wiki/index.md 种子（仅当缺失时写入）—— 数仓入口结构
# ------------------------------------------------------------------------------
INDEX_FILE=knowledge/wiki/index.md
if [[ ! -s "$INDEX_FILE" ]]; then
  TODAY="$(date +%Y-%m-%d)"
  cat > "$INDEX_FILE" <<EOF
---
title: 数仓知识库索引
type: topic
updated: ${TODAY}
---

# 数仓知识库索引

此索引由 LLM 在每次摄取 / lint / merge 后自动重建。
**请勿手动编辑。**

## 概览（Overview）
<!-- wiki/overview/*.md -->

## 业务域（Domains）
<!-- wiki/domains/*.md -->

## 指标（Metrics）
<!-- wiki/metrics/*.md -->

## 表（Tables）
<!-- wiki/tables/*.md -->

## 业务语义（Business）
<!-- wiki/business/*.md -->

## 风险与坑位（Risks）
<!-- wiki/risks/*.md -->

## 规范（Rules）
<!-- wiki/rules/*.md -->

## 通用概念（Concepts）
<!-- wiki/concepts/*.md -->

## 专题（Topics）
<!-- wiki/topics/*.md -->

## 地图（Maps）
<!-- wiki/maps/*.md -->

## 实体（Entities）
### 人物（People）
### 组织（Organizations）
### 产品（Products）
EOF
  echo "✓ 写入种子索引：${INDEX_FILE}"
else
  echo "· 保留已有的 ${INDEX_FILE}"
fi

# ------------------------------------------------------------------------------
# 4. .env 引导（仅当缺失时从 .env.example 复制）
# ------------------------------------------------------------------------------
if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "✓ 已从 .env.example 复制 .env —— 请编辑并填写 KNOWLEDGE_ROOT_DIR=${REPO_ROOT}"
  else
    echo "! 未找到 .env.example，跳过 .env 生成"
  fi
else
  echo "· 保留已有的 .env"
fi

# ------------------------------------------------------------------------------
# 5. Skill 同步 —— skills/ → .trae/skills/
# ------------------------------------------------------------------------------
# skills/         版本化的 Skill 源（跟随 git 分发，含 SKILL.md 英文与 SKILL.zh.md 中文副本）
# .trae/skills/   Trae 运行时缓存（本机自动发现，不入 git）
#                 Trae IDE 打开工程后一般会自建/镜像该目录，此脚本仅在 IDE 未启动或首次 clone
#                 时兜底同步一份。每个 skill 目录只同步英文 SKILL.md 作为 Trae 加载入口；
#                 中文副本 SKILL.zh.md 不同步，避免同名 skill 触发词冲突。
if [[ -d skills ]]; then
  mkdir -p .trae/skills
  synced=0
  skipped=0
  for src in skills/*/SKILL.md; do
    [[ -f "$src" ]] || continue
    name="$(basename "$(dirname "$src")")"
    dst=".trae/skills/${name}/SKILL.md"
    mkdir -p "$(dirname "$dst")"
    if [[ -f "$dst" ]] && cmp -s "$src" "$dst"; then
      skipped=$((skipped + 1))
    else
      cp "$src" "$dst"
      synced=$((synced + 1))
    fi
  done
  echo "✓ Skill 同步：${synced} 个已更新，${skipped} 个未变化 → .trae/skills/"
else
  echo "· 未找到 skills/ 目录，跳过 Skill 同步"
fi

# ------------------------------------------------------------------------------
# 完成
# ------------------------------------------------------------------------------
echo ""
echo "初始化完成。"
echo ""
echo "下一步："
echo "  1. 编辑 .env，将 KNOWLEDGE_ROOT_DIR 设为：${REPO_ROOT}"
echo "  2. Trae 会自动加载 .trae/skills/ 下的 Skill；其他宿主请手动加载 skills/ 目录"
echo "  3. 在宿主里打开 knowledge/ 目录，AIDE.md 会被自动加载"
echo "  4. 试试：\"把这份飞书文档摄取进知识库\"、\"lint 一下 wiki\"、\"生成本周 digest\""
