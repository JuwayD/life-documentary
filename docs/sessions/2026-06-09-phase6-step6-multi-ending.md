# 2026-06-09 Phase 6 Step 6: 多结局系统

## 本次目标

按 roadmap 推进 Phase 6 多结局:让主线/支线可被 GM 自然收束,并把结局作为结构化状态展示。

## 实现内容

- 新增 `ending_seeds` 世界 flag:公堂昭雪、私下和解、远走扬州三类收束方向。
- 新增 `list_endings` read tool:读取可用结局种子与已记录进度。
- 新增 `record_ending` write tool:记录候选/已达成结局,支持 `final=true` 标记终局。
- 注册两个新工具到 LLM tools registry。
- GM Agent 提示词新增多结局工作流。
- 前端新增结局面板,展示结局方向或已达成结局。
- 新增 read/write/registry/stream/server/scenario 覆盖测试。

## 设计原则

- 结局条件不写死在代码中,由 GM 结合证据链、NPC 态度、压力钟、法律和近期事件判断。
- `ending_seeds` 是参考素材,不是任务完成条件。
- `record_ending` 只持久化 GM 的判断结果,不自动触发奖惩或状态清算。

## 下一步

继续推进 Phase 6 的可分享存档。
