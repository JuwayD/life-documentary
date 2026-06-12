# 2026-06-11 Phase 13: NPC 扩展

## 目标

扩展 NPC 数量从 30 到 34,填补稀疏地点,达到 vision 目标 30+。

## 变更

### Bug 修复
- **Web 服务器缺少 Phase 12 种子**: `server.py` 的 `seed_all()` 未调用 `seed_yangzhou_phase12`,导致 Web 用户只有 26 个 NPC 而非 30 个。已修复。

### 新增 NPC (Phase 13)
4 个新 NPC 填补稀疏地点:

| ID | 名称 | 地点 | 职业 | 特点 |
|---|---|---|---|---|
| `flower_girl_mei` | 梅儿 | street_main | 卖花女 | 街市消息灵通,5 段日程 |
| `scholar_huang` | 黄老秀才 | academy_gate | 落第秀才 | 可教古文/书法,4 段日程 |
| `washerwoman_liu` | 刘婶 | ferry_pier | 洗衣妇 | 渡口低频背景 NPC |
| `gatekeeper_wu` | 吴门子 | court_yard | 府衙门子 | 衙门往来记录者,高频演化 |

### 新增支线素材
- **门子账簿**: 吴门子记录了一个常来衙门却不挂号的神秘人
- **渡口夜货**: 刘婶目睹码头半夜搬运贴封条的箱子

### 文件变更
- `src/mingrpg/scenarios/yangzhou_phase13.py` — 新建,4 NPC + 2 支线
- `src/mingrpg/web/server.py` — 修复 seed_all 添加 phase12,新增 phase13
- `src/mingrpg/cli.py` — 新增 phase13 种子调用
- `tests/scenarios/test_scenarios.py` — 新增 11 个测试
- `.plan.md` — 更新 NPC 计数和测试数量

## 测试结果

- 74 个场景测试全部通过(含 11 个新测试)
- 完整测试套件: 441 passed, 2 failed(均为预存问题), 4 skipped

## 决策

- Phase 13 命名延续 Phase 12 的模式(虽然 Phase 12 未在 .plan.md 中列出)
- 选择填补稀疏地点而非随机添加,提升世界密度
- 门子(wu)设置为 every_3_turns 高频演化,因其记录衙门往来对叙事价值高
