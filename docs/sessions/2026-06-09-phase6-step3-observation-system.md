# 2026-06-09 Phase 6 Step 3: 观察系统

## 本次目标

按路线图推进 Phase 6 观察系统:让地点与 NPC 拥有可发现细节,玩家可通过观察发现更多信息,但代码不判断线索意义。

## 实现内容

- 新增 `list_observables` read tool。
- 新增 `discover_observation` write tool。
- 注册两个工具到 LLM tools registry。
- 在 GM system prompt 中加入观察系统规则与工作流程。
- 开场场景加入可观察细节:
  - 府衙大堂公案上的状纸细节。
  - 侧屏后的隐约动静。
  - 刘师爷袖口朱砂批痕。
  - 刘师爷书袋纸角。
- 玩家增加 `observation=10`。
- Web UI 增加观察面板与“仔细观察”按钮。
- 增加 read/write/LLM/scenario/web/E2E 覆盖测试。

## 设计原则

- `observable_details` 是素材,不是任务条件。
- `discover_observation` 只记录发现事实,不生成建议、线索或后果。
- 是否需要 `record_clue` 由 GM 根据叙事语境决定。
- 复用现有 turn loop,不新增 API endpoint。

## 下一步

可继续扩展各地点/NPC 的观察素材,并让高门槛细节通过 `skill_check` 与玩家属性/处境联动。
