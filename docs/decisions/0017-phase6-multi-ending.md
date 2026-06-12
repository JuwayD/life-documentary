# ADR-0017: Phase 6 多结局系统

## 状态

Accepted

## 背景

Phase 6 下一项是多结局。项目原则要求代码只做状态读写,不在代码层判断任务完成或结局条件。

## 决策

- 新增 `ending_seeds` 世界 flag,保存可供 GM 参考的结局方向。
- 新增 `list_endings` read tool,返回结局种子与已记录进度。
- 新增 `record_ending` write tool,记录已达成或候选结局。
- `record_ending(final=true)` 只标记主线正式收束,不触发额外规则。
- 前端新增结局面板,没有已达成结局时展示可参考方向;已有结局时展示摘要与终局标记。

## 后果

- GM 可以根据线索、NPC 态度、压力钟、法律与近期事件自然收束剧情。
- 代码不硬编码“好/坏结局”条件,仍符合“代码是手脚,AI 是大脑”。
- 后续可在可分享存档中包含 `ending_progress`。
