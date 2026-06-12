# 会话日志: Phase 6 Step 2 顾问系统

**日期**: 2026-06-09

## 做了什么

### 种子数据
- `yangzhou_court.py`: shiye 追加 `is_advisor` / `advisor_topics` / `advisor_style`
- `yangzhou_market.py`: teahouse_owner 追加顾问属性
- `yangzhou_districts.py`: teacher_gu 追加顾问属性

### 新工具
- `tools/write.py`: `ask_advisor` — 记录请教 + 返回顾问资料
- `tools/read.py`: `list_advisors` — 列出所有顾问(可选按地点过滤)
- `tools_registry.py`: 注册两个工具,含 Anthropic 格式 schema

### GM Agent 提示词
- `agent.py` SYSTEM_PROMPT 新增"顾问系统"章节
- 工作流程加入"请教顾问 → ask_advisor"

### 前端
- `index.html`: 新增顾问 panel section (`data-test="advisor-panel"`)
- `app.js`: 新增 `renderAdvisorPanel()` — 过滤 is_advisor NPC,优先显示同地点,显示 topics + 请教按钮
- `style.css`: 新增 `.advisor-card` / `.advisor-topic` / `.advisor-ask` 样式

### 测试 (新增 14 个)
- `test_scenarios.py`: 2 个 — 顾问属性种子 + 保留原有契约
- `test_write.py`: 4 个 — ask_advisor 正常/未知/非顾问/空问题
- `test_read.py`: 3 个 — list_advisors 返回/过滤/空世界
- `test_agent_stream.py`: 2 个 — registry + stream 执行
- `test_server.py`: 1 个 — snapshot 包含顾问属性
- `test_e2e_browser.py`: 2 个 — 面板显示 + 请教按钮

### 测试结果
```
185 passed, 4 skipped (live LLM), 15 warnings in ~10s
```

## 未做

- 观察系统 (Phase 6 后续)
- 多角色队伍 / 修炼 / 存档 (远期)
