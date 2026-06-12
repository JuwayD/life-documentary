# 2026-06-12 Phase 28: NPC 对话系统

## 完成内容

### 对话工具
- `get_npc_dialogue`(read): 按态度值过滤 NPC 可用对话选项(问候/话题/告别/特殊)
- `record_dialogue`(write): 记录对话交互(记忆/态度/事件)

### NPC 对话素材
为 12 个关键 NPC 添加了 `dialogue_lines`:
- 扬州府衙: 王知府、刘师爷
- 扬州街市: 陈掌柜、乞丐老刘
- 扬州客栈: 赵掌柜、马行商
- 主线反派: 赵三、吴员外
- 女性 NPC: 柳姑娘、宋婶、周寡妇、阿杏

### 系统集成
- tools_registry.py: 注册 get_npc_dialogue / record_dialogue
- replay.py / audit/logger.py: record_dialogue 加入可重放/审计集合
- GM 系统提示词: 新增"NPC 对话系统"章节 + 工作流程步骤 7b

### 前端面板
- 右栏"对话"面板: 展示附近 NPC 的态度状态、可用话题数、特殊台词
- "交谈"快捷按钮

### 测试
- 8 个 get_npc_dialogue 测试(态度过滤/话题解锁/特殊触发/错误处理)
- 9 个 record_dialogue 测试(记忆/态度/事件/错误处理)
- 总计 596 测试通过

### 文档
- ADR-0114
- 会话日志
- README / .plan.md 更新
