# ADR-0109: Phase 23 — Main Story Progression (Cross-Region Investigation)

## Status

Accepted

## Context

After completing 22 phases (including 4 new regions: Guazhou, Nanjing, Suzhou, Hangzhou), the project had scattered regional threads all referencing merchant_wu but no unified investigation arc. The .plan.md listed "主线剧情推进 — 科场弊案/盐税调查与扬州主线联动" as the next direction.

The existing regional threads (Guazhou night crossing, Nanjing exam scandal & salt tax, Suzhou silk conspiracy, Hangzhou tea smuggling) all connect to merchant_wu but operate independently. Players visiting multiple regions would encounter related clues but have no way to track cross-region progress.

## Decision

Implement Phase 23 as a **gameplay feature** (not a new region) that:

1. **Cross-region investigation thread** ("江南暗网"): A unified thread that spans all 5 regions, with merchant_wu as the central connecting figure. Attached to story_seeds as a side thread with anchors in all regions.

2. **Quest log system**: New tools `update_quest_log` and `list_quest_log` for tracking investigation milestones. 7 milestones seeded at startup (状纸递出 → 夜渡暗货 → 科场旧事 → 盐税暗线 → 丝税账簿 → 龙井暗运 → 对质吴员外). Milestones progress through locked → active → completed.

3. **New pressure clock** ("朝廷风声"): Tracks imperial court awareness of the Jiangnan merchant network. danger_at=5. As investigation deepens, the clock advances, adding narrative tension.

4. **Expanded endings**: 3 new ending directions (暗网瓦解/半壁揭开/暗网反噬) for cross-region outcomes, in addition to the 3 original Yangzhou endings.

5. **Agent prompt update**: New "跨地域调查" section in GM system prompt explaining the quest log, milestone progression, court_wind clock, and cross-region investigation guidance.

6. **Snapshot enhancement**: Quest log active/completed entries shown in the GM snapshot summary.

## Consequences

- **Positive**: Players can now track cross-region investigation progress. GM has structured guidance for handling multi-region evidence chains. The quest log provides a clear narrative arc without constraining emergent gameplay.
- **Positive**: The investigation remains optional — players can still engage with individual regions independently.
- **Neutral**: No new locations or NPCs added. The cross-region thread attaches to existing entities and locations.
- **Risk**: The quest log is GM-driven (not code-enforced), so milestone progression depends on the LLM correctly identifying cross-region evidence. This is consistent with the project's "code is hands, AI is brain" philosophy.
