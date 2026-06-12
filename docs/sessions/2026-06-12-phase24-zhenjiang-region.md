# Session: Phase 24 — Zhenjiang Region (镇江)

**Date**: 2026-06-12
**Duration**: ~15 minutes
**Focus**: Add Zhenjiang as a new region (Phase 24)

## What was done

1. **Created `src/mingrpg/scenarios/zhenjiang.py`**:
   - 3 locations: Xijin Ferry (西津渡口), Zhenjiang Fortress (镇江卫所), Jinshan Temple (金山寺)
   - 3 NPCs: Commander Liu (刘指挥使), Monk Liaofan (了凡禅师), Ferryman Ma (马渡子)
   - 1 side thread: "卫所扣货" (Seized Cargo at the Garrison)
   - `seed_zhenjiang()` function with all standard wiring (exits, evolution registry, story seeds, rumor hooks)

2. **Updated entry points**:
   - `src/mingrpg/cli.py`: Added import and seed call
   - `src/mingrpg/web/server.py`: Added import and seed call in `seed_all()`

3. **Added 10 tests** in `tests/scenarios/test_scenarios.py`:
   - Location creation and naming
   - NPC creation and attributes
   - Service catalogs (military escort, cargo inspection, ferry crossings)
   - Geographic connection (Guazhou → Zhenjiang exit)
   - Side thread creation
   - Flag setting
   - Duplicate seeding prevention
   - Rumor hook attachment

4. **Updated documentation**:
   - `.plan.md`: Added Phase 24, updated NPC/location counts, reordered next steps
   - `README.md`: Added Phase 24 summary, updated test count
   - `docs/decisions/0110-phase24-zhenjiang-region.md`: ADR documenting the decision
   - `docs/sessions/2026-06-12-phase24-zhenjiang-region.md`: This session log

## Key decisions

- **Location choice**: Zhenjiang fills the geographic gap between Guazhou (north bank) and Nanjing. Historically a military garrison town at the Yangtze-Canal confluence.
- **Military angle**: The side thread involves a garrison seizing smuggled cargo, adding a new dimension to the "江南暗网" investigation (military cover for smuggling).
- **Pattern adherence**: Followed the established 3+3+1 pattern (3 locations, 3 NPCs, 1 side thread) for consistency.

## Test results

All 178 scenario tests pass (including 10 new Zhenjiang tests).

## Next steps

The .plan.md now lists these as next directions (ordered):
1. 前端 replay 播放器增强 — 可视化回放事件溯源存档
2. 前端调查面板 — 在侧栏展示调查日志和跨地域进度
3. 更多新地域 — 更多江南城市或北方重镇
