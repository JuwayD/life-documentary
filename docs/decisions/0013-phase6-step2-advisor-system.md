# ADR-0013: Phase 6 Step 2 顾问系统

## 状态

已接受 (2026-06-09)

## 背景

Phase 6 Step 1 完成了前端剧情面板。下一步路线图目标:玩家不知下一步做什么时,可向顾问 NPC 请教,帮助规划下一步行动。

## 决策

### 1. 复用现有 NPC 属性,不新增 DB schema

顾问标识 (`is_advisor`, `advisor_topics`, `advisor_style`) 放在 NPC 的 `attributes` 字典中,不新增表字段。与现有 `personality`/`memories`/`rumor_hooks` 同级。

### 2. 不新增 API endpoint

顾问对话流通过现有 REST/WS turn loop 完成。前端按钮通过 `handleTurn()` 发送自然语言"请教"文本,GM Agent 在回合内调用 `ask_advisor` 工具。

### 3. ask_advisor 只记录不生成

`ask_advisor` 工具只做三件事:
- 校验顾问身份
- 记录 memory + event
- 返回顾问资料供 LLM 生成建议

建议内容由 GM Agent 以顾问口吻生成,保持"代码是手脚,AI 是大脑"原则。

### 4. 顾问是 NPC,不是系统攻略

- 顾问根据其 personality、knowledge scope 给出建议
- 可以偏见、隐瞒、误判
- 只给 1-3 个方向,不替玩家决定
- 不在附近时可提示前往,不强制

### 5. 最小范围:3 名顾问

- 刘师爷 (府衙程序/状纸策略/官场风险)
- 陈掌柜 (街市传闻/人情世故/找证人)
- 顾先生 (讼状/旧案/读书人关系)

## 后果

- 前端新增顾问面板 (在"附近的人"与"主线剧情"之间)
- 新增 2 个工具 (`ask_advisor` / `list_advisors`)
- GM Agent 提示词新增顾问章节
- 新增 14 个测试 (185 total,全过)
