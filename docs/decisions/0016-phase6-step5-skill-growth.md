# ADR-0016: Phase 6 Step 5 修炼/技能成长系统

## 状态

已接受 (2026-06-09)

## 背景

Phase 6 Step 4 完成了多角色队伍系统。路线图下一步目标:让技能成长有结构化的修炼和学习路径,而非仅靠原始的 advance_skill 直接调整数值。

## 决策

### 1. 新增 train_skill 工具:自主修炼

`train_skill` 记录一次修炼/练习并授予经验。与 `advance_skill` 的区别:
- `train_skill` 语义明确:"我练了书法",xp_granted 由 GM 根据叙事决定
- `advance_skill` 保留用于直接数值调整(突破升级、GM 任意增减)

代码只执行经验加算和事件记录,不判断是否成功。

### 2. 新增 learn_from_npc 工具:向NPC学习

`learn_from_npc` 记录向 NPC 学习并授予经验:
- 校验教师是 NPC
- 自动记录教师记忆("XXX向我学习了YYY")
- 记录世界事件

代码只记录关系和经验,学习效果由 GM 根据叙事判断。

### 3. NPC 增加 skills_taught 属性

在有教学能力的 NPC 上添加 `skills_taught` 列表:
- 顾先生: litigation, calligraphy
- 何郎中: medicine
- 陈掌柜: persuasion

GM Agent 通过读取此属性判断 NPC 能否教授某技能。

### 4. 前端技能面板增强

- 技能卡片增加等级标签 (Lv.X)
- 增加经验进度条 (xp/needed)
- 经验公式: level*10 + 5 (level 0→1 需 5, 1→2 需 15, ...)

### 5. Agent 提示词扩展

将原来笼统的"修炼与技能成长"拆分为三个明确工作流:
- 自主修炼 → train_skill
- 向 NPC 学习 → learn_from_npc
- 突破升级 → advance_skill(level_delta=1)

同时说明技能等级可作为 skill_check 的 modifier。

## 后果

- 新增 2 个 write 工具 (`train_skill` / `learn_from_npc`)
- 3 名 NPC 新增 `skills_taught` 属性
- 前端技能面板增加等级标签和经验进度条
- Agent 提示词新增三个修炼工作流
- 新增 11 个测试 (225 total,全过)
