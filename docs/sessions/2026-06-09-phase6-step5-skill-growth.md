# 2026-06-09 Phase 6 Step 5: 修炼/技能成长系统

## 本次目标

按 roadmap 推进 Phase 6 修炼/技能成长:让技能成长有结构化的修炼和学习路径,而非仅靠原始的 advance_skill 直接调整数值。

## 实现内容

- 新增 `train_skill` write tool:记录修炼/练习并授予经验。
- 新增 `learn_from_npc` write tool:记录向 NPC 学习并授予经验,自动记录教师记忆。
- 3 名 NPC 新增 `skills_taught` 属性(顾先生/何郎中/陈掌柜)。
- 注册两个新工具到 LLM tools registry。
- GM Agent 提示词扩展为三个修炼工作流(自主修炼/向NPC学习/突破升级)。
- 前端技能面板增强:等级标签 + 经验进度条。
- 新增 11 个 read/write 覆盖测试。

## 设计原则

- `train_skill` 与 `advance_skill` 职责分离:train_skill 是语义化的修炼记录,advance_skill 是原始数值调整。
- `learn_from_npc` 自动记录教师记忆,保持"代码是手脚,AI 是大脑"原则。
- NPC 的 `skills_taught` 是参考数据,GM Agent 自行判断能否教授。
- 技能等级可作为 skill_check 的 modifier,但由 GM 决定何时使用。

## 下一步

可继续推进 Phase 6 的多结局或可分享存档。
