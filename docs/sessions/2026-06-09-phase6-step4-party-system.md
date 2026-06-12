# 2026-06-09 Phase 6 Step 4: 多角色队伍系统

## 本次目标

按 roadmap 推进 Phase 6 多角色队伍:让玩家可与 NPC 形成同行关系,并可指定当前行动角色,但代码不判断 NPC 意愿或行动策略。

## 实现内容

- 新增 `list_party` read tool。
- 新增 `join_party` / `leave_party` / `set_active_actor` write tools。
- 注册四个工具到 LLM tools registry。
- 在 GM system prompt 中加入多角色队伍规则与工作流程。
- Web UI 增加“队伍”面板:
  - 默认显示玩家。
  - 显示成员角色、位置、当前行动标记。
  - 队友提供“让其行动”快捷按钮。
- FakeAgent 测试支持同行和切换行动角色。
- 增加 read/write/LLM/web/E2E 覆盖测试。
- 更新 README 与 roadmap。

## 设计原则

- `flags.party` 是队伍事实记录,不是队友服从规则。
- `join_party` / `leave_party` 只记录关系、记忆和事件。
- `set_active_actor` 只记录当前由谁出面,不代替 GM 判断行动结果。
- 复用现有 REST/WS turn loop,不新增 API endpoint。

## 下一步

可继续推进 Phase 6 的修炼/技能成长、多结局或可分享存档。若继续扩展队伍,优先考虑队友跟随移动、关系/信任值、队友战斗站位等小切片。
