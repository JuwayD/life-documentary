# ADR-0015: Phase 6 Step 4 多角色队伍系统

日期: 2026-06-09
状态: accepted

## 背景

Phase 6 的下一项玩法是多角色队伍。项目第一原则仍是“代码是手脚,AI 是大脑”:代码不能判断 NPC 是否愿意加入、谁该行动、队友是否服从,只能记录队伍关系并暴露状态给 GM。

## 决策

实现最小垂直切片:

1. 队伍状态存入 `flags.party`:
   - `leader_id`
   - `active_actor_id`
   - `members[{entity_id, role, joined_reason}]`
2. 新增 read tool `list_party(leader_id="player")`:
   - 返回队伍成员、角色、位置、性格摘要与当前行动角色。
3. 新增 write tools:
   - `join_party(entity_id, leader_id="player", role="同伴", joined_reason="")`
   - `leave_party(entity_id, leader_id="player", reason="")`
   - `set_active_actor(entity_id, leader_id="player", reason="")`
4. 写工具只记录关系变化、NPC 记忆和事件,不判断是否应该加入/离开。
5. GM prompt 增加队伍规则:
   - 邀请/雇佣/说服 NPC 同行前先读状态与性格。
   - 判断成立后调用 `join_party`。
   - 离队调用 `leave_party`。
   - 队友代为行动调用 `set_active_actor`。
6. 前端增加“队伍”面板:
   - 默认显示玩家。
   - 显示队友、角色、位置和当前行动标记。
   - 队友提供“让其行动”快捷按钮,复用现有 turn loop。

## 取舍

- 不新增数据库 schema,继续用 flags JSON。
- 不新增 API endpoint,前端只渲染 snapshot。
- 不实现自动队友跟随、阵型、共享背包或队友 AI;这些都需要更多规则,暂时交给 GM 叙事和现有工具处理。
- 不把队友当作玩家工具;队友仍是有记忆、性格、利益和风险的 NPC。

## 后果

玩家可以通过自然语言邀请 NPC 同行,并在 UI 中看到队伍状态。GM 可让队友出面交涉、观察或带路,但所有意愿、风险和后果仍由 GM 根据世界状态判断。未来可在此基础上加入队友关系值、跟随移动、队伍战斗站位与多角色成长。
