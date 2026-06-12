# Session: Phase 22 — Hangzhou Region (杭州)

**Date**: 2026-06-12
**Scope**: New region —杭州

## Summary

Added杭州 as the fourth explorable region outside扬州, following the established pattern from Phase 17/20/21.

## Changes

### New files
- `src/mingrpg/scenarios/hangzhou.py` — 3 locations, 3 NPCs, 1 side thread, seed function

### Modified files
- `src/mingrpg/cli.py` — added Hangzhou seed import + call
- `src/mingrpg/web/server.py` — added Hangzhou seed import + call in `seed_all()`
- `src/mingrpg/llm/agent.py` — added杭州 region description + 3 NPC entries to SYSTEM_PROMPT
- `tests/scenarios/test_scenarios.py` — added 21 standard region tests
- `docs/decisions/0108-phase22-hangzhou-region.md` — ADR
- `.plan.md` — updated project status
- `README.md` — updated project scale

## Design

| Element | Details |
|---------|---------|
| Locations | 西湖, 灵隐寺, 拱宸桥码头 |
| NPCs | 方掌柜 (茶商), 明空方丈 (方丈), 孙船老大 (船老大) |
| Side thread | 龙井暗运 — 茶叶走私, 连接扬州吴员外 + 苏州丝税 |
| Connection | 苏州枫桥 ↔ 杭州拱宸桥码头 |

## Test results

- 21 new region tests: all passing
- Full suite: 527 passed, 4 skipped (LLM integration), 1 flaky E2E (pre-existing)
