# Session Log: Phase 27 — 新地域 (淮安)

**日期**: 2026-06-12
**目标**: 新增淮安区域,扩展跨地域调查网络

## 完成内容

### 新地域:淮安
- 创建 `src/mingrpg/scenarios/huaian.py`
  - 3 个地点:清江浦、漕运总督府、玄妙观
  - 3 个 NPC:何总督(漕运总督)、赵牙人(运河牙人)、清虚子(道观住持)
  - 1 条支线素材"漕运暗流"
  - seed 函数 + 演化注册表 + 故事种子 + 谣言钩子

### 跨地域调查更新
- 更新 `src/mingrpg/scenarios/phase23_main_story.py`
  - CROSS_REGION_THREAD anchors 新增淮安 4 个锚点
  - 新增调查里程碑 `ha_grain_trail`
  - merchant_wu network_regions 扩展至 6 地
  - hook/stakes 文本更新,不再硬编码"四地"

### GM 系统提示词更新
- 更新 `src/mingrpg/llm/agent.py`
  - 【地域】新增镇江和淮安描述(补上 Phase 24 遗漏)
  - 新增【镇江 NPC】和【淮安 NPC】章节
  - 【跨地域调查】更新为多地网络

### 测试
- 新增 18 个覆盖测试到 `tests/scenarios/test_scenarios.py`
  - 地点创建、NPC 创建、NPC 属性、服务目录、价格表
  - 出口连接、内部连通、演化注册表、支线素材
  - 故事线程、谣言钩子、flag 设置、幂等性
  - 日程、背包、观察细节、标签
- 修复 2 个因文本变更导致的既有测试断言

### 文档
- ADR-0113
- README.md 更新(Phase 27 条目)
- 04-roadmap.md 更新(Phase 27 条目)

## 测试结果

- 579 单元测试全部通过
- 196 场景测试全部通过(含 18 个新增)
- E2E 测试 1 个 flaky(与本次变更无关)

## 决策理由

选择"更多新地域"方向,原因:
1. roadmap 列出的第一个可选方向
2. 淮安作为漕运枢纽与跨地域调查主线天然契合
3. 可独立验收,不影响现有功能
