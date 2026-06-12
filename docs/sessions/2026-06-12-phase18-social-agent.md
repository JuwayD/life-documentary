# 2026-06-12 Phase 18: 社交专家 Agent

## 目标

新增 SocialAgent 作为第二个专业 Agent，处理说服、欺骗、威吓、议价、察言观色等社交互动。

## 变更

### 新增文件
- `src/mingrpg/llm/agents/social.py` — SocialAgent 类
- `docs/decisions/0104-phase18-social-agent.md` — 架构决策记录

### 修改文件
- `src/mingrpg/llm/agents/__init__.py` — 导出 SocialAgent
- `src/mingrpg/llm/tools_registry.py` — 注册 social agent 到 delegate_to_agent
- `src/mingrpg/llm/agent.py` — GM 系统提示词增加社交 Agent 委托指引
- `tests/llm/test_multi_agent.py` — 新增 19 个测试用例

## 新增内容

### SocialAgent
- 继承 AgentBase，agent_id = "social"
- 支持 5 种互动类型：persuasion/deception/intimidation/negotiation/insight
- 复用现有工具：skill_check, add_memory, set_attribute, add_status, transfer_money, log_event
- NPC 态度系统：态度值 -100~+100，检定结果影响态度变化
- 议价规则：CHA 检定成功可降价 10-50%

### GM Agent 更新
- 多 Agent 协作章节增加 social agent 描述和委托指引
- 工作流程增加社交委托步骤（4b）

## 测试结果

- 19 个新测试全部通过
- 总测试数：535（+19）
- 全量测试通过（1 个 flaky E2E 测试在隔离运行时通过）

## 决策

- 复用现有工具而非创建新工具：social agent 使用与 combat agent 相同的底层工具，只是系统提示词和上下文不同
- 态度系统通过 set_attribute 实现，不引入新的状态管理层
- 5 种互动类型覆盖了明代背景 RPG 的核心社交场景
