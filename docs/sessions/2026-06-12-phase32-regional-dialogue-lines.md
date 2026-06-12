# Session: Phase 32 — Regional NPC Dialogue Lines

**Date**: 2026-06-12
**Objective**:补全苏州/杭州/淮安/镇江 12 个 NPC 的 dialogue_lines

## What Was Done

### Dialogue Lines Added (12 NPCs)

**苏州 suzhou.py**:
- `silk_merchant_qian` 钱掌柜: 丝绸生意/扬州商帮话题
- `garden_keeper_shen` 沈园丁: 园中来客/假山密室话题
- `canal_boatman_feng` 冯船家: 夜半船声/运河官兵话题

**杭州 hangzhou.py**:
- `tea_merchant_fang` 方掌柜: 茶路生意/扬州暗线话题
- `abbot_mingkong` 明空方丈: 寺中来客/官场往来话题
- `canal_captain_sun` 孙船老大: 运河近况/暗舱生意话题

**淮安 huaian.py**:
- `grain_governor_he` 何总督: 漕运调度/商帮暗流话题
- `canal_broker_zhao` 赵牙人: 码头动向/暗中勾当话题
- `daoist_qingxu` 清虚子: 运河之事/何总督话题

**镇江 zhenjiang.py**:
- `fortress_commander_liu` 刘指挥使: 卫所防务/扣货之事话题
- `jinshan_monk` 了凡禅师: 寺中来客/扬州之事话题
- `xijin_ferryman` 马渡子: 夜间渡江/卫所扣货话题

### Tests Added
- 12 new tests in `tests/scenarios/test_scenarios.py`
- Extracted `_assert_dialogue_structure` helper to reduce duplication
- 230 scenario tests pass

### Docs Updated
- `.plan.md`: Phase 32 status
- `docs/04-roadmap.md`: Phase 32 section
- `README.md`: Phase 32 completion entry
- `docs/decisions/0118-phase32-regional-dialogue-lines.md`: ADR

## Key Insight

All 12 missing NPCs were from the 4 later-stage regional expansion files (Phase 21-24). The pattern was consistent: these files were created before the dialogue system was introduced in Phase 28, and the dialogue backfill in Phase 28/29 only covered Yangzhou and Xuzhou.
