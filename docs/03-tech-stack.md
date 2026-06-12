# 技术栈选型

## 核心

| 层级 | 选型 | 理由 |
|---|---|---|
| **编程语言** | Python 3.11+ | AI 生态最好,工具库丰富,团队熟练 |
| **LLM** | Claude Sonnet 4.6 (API) | 最佳 Tool Use 能力,性价比好 |
| **状态存储** | SQLite (Python stdlib) | 零依赖、持久化、无需服务器 |
| **测试** | pytest 8.x + pytest-cov | 行业标准,TDD 基础设施 |

## 工具层

| 需求 | 选型 | 理由 |
|---|---|---|
| 法条检索 | 关键词匹配 (Phase 0) | 复杂度低,Phase 1+可升向量 |
| 掷骰 | 自实现 (5 行代码) | 纯随机数,不需要库 |
| Schema 校验 | `dataclasses` (stdlib) | 够用,无外部依赖 |
| CLI 交互 | `input()` + `rich` | 简单美观;Phase 0 不到 CLI parser |

## AI 集成

| 需求 | 选型 | 理由 |
|---|---|---|
| LLM API | `anthropic` SDK v0.39+ | 官方维护 |
| Tool Use | Claude Tool Use 原生 | 本身就是为这个场景设计的 |
| Token 管理 | 自实现窗口控制 | Phase 0 简单截断即可 |
| 缓存 | 自实现 LRU dict | API 调用频率低,不需要 Redis |

## 存储

| 数据 | 格式 | 理由 |
|---|---|---|
| 实体/位置 | SQLite 表 | 结构化,可查询 |
| 法条/民俗 | YAML 文件 | 人类可读可写 |
| NPC 记忆 | SQLite (entity_memories) | 结构化,关联 entity |
| 审计日志 | JSONL (文件系统) | append-only,每行独立有效 |
| 世界快照 | JSON (存档) | 一次写入,用于回放 |
| 剧情 Flag | SQLite key-value | 简单直接 |

## 依赖为什么这么少

设计哲学:**
- Python 标准库已经提供了 SQLite、json、dataclasses、unittest
- 外部依赖仅限 `anthropic` SDK 和 `pytest` + `rich`
- 越少依赖 = 越少版本冲突 = AI 加功能时 context 越小

## Phase 0 依赖清单

```toml
# pyproject.toml
[project]
dependencies = [
    "anthropic >= 0.39, < 1.0",
    "rich >= 13.0",
]

[project.optional-dependencies]
dev = [
    "pytest >= 8.0",
    "pytest-cov >= 5.0",
]
```

**总计 2 个运行时依赖 + 2 个开发依赖。**