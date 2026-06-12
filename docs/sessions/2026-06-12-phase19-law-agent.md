# 2026-06-12 Phase 19: 法律专家 Agent

## 目标

新增 LawAgent 作为第三个专业 Agent，处理法条检索、量刑分析、司法程序等法律事务。

## 变更

### 新增文件
- `src/mingrpg/llm/agents/law.py` — LawAgent 类
- `docs/decisions/0105-phase19-law-agent.md` — 架构决策记录

### 修改文件
- `src/mingrpg/llm/agents/__init__.py` — 导出 LawAgent
- `src/mingrpg/llm/tools_registry.py` — 注册 law agent 到 delegate_to_agent
- `src/mingrpg/llm/agent.py` — GM 系统提示词增加法律 Agent 委托指引
- `tests/llm/test_multi_agent.py` — 新增 20 个测试用例

## 新增内容

### LawAgent
- 继承 AgentBase，agent_id = "law"
- 支持 4 种案件类型：criminal(刑事)/civil(民事)/procedural(程序)/administrative(行政)
- 5 个工具：query_laws, log_event, add_memory, set_attribute, add_status
- 法条自动提取：从 query_laws 调用结果中提取适用法条列表
- 上下文支持：defendant_id, charges, legal_context(含 victim_id/witness_ids/evidence/severity)

### GM Agent 更新
- 多 Agent 协作章节增加 law agent 描述和委托指引
- 工作流程增加法律委托步骤（3b）
- delegate_to_agent 工具描述和上下文说明同步更新

## 测试结果

- 20 个新测试全部通过
- 总测试数：550（+15）
- 全量测试通过（1 个 flaky E2E 测试在隔离运行时通过）

## 决策

- 复用现有工具而非创建新工具：law agent 使用 query_laws + 写工具，与 GM 共享底层实现
- 法条检索通过 query_laws 工具完成，不引入新的检索机制
- 4 种案件类型覆盖了明代司法体系的核心场景
- 法条自动提取功能方便 GM 快速获取适用法条列表
