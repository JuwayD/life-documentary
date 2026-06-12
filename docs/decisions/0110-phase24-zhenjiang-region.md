# ADR-0110: Phase 24 — New Region (Zhenjiang / 镇江)

## Status

Accepted

## Context

After Phase 23 unified the cross-region investigation arc, the project had 5 regions (Yangzhou, Guazhou, Nanjing, Suzhou, Hangzhou) all connected through the "江南暗网" thread. The .plan.md listed "更多新地域 — 更多江南城市或北方重镇" as an optional next direction.

Zhenjiang (镇江) is a historically significant strategic location at the confluence of the Yangtze River and the Grand Canal. It was a key military garrison town (镇江卫) guarding the river crossing between Yangzhou (north bank) and the southern regions. This makes it a natural extension of the existing geography — players traveling from Guazhou southward would logically pass through Zhenjiang.

## Decision

Implement Phase 24 as a **new region** following the established pattern (3 locations, 3 NPCs, 1 side thread):

1. **Locations**:
   - `zhenjiang_xijin` (西津渡口): Ancient ferry crossing on the south bank, connecting to Guazhou via exit
   - `zhenjiang_fortress` (镇江卫所): Military garrison compound, restricted access
   - `zhenjiang_jinshan` (金山寺): Famous Buddhist temple on Golden Hill

2. **NPCs**:
   - `fortress_commander_liu` (刘指挥使): Garrison commander, strict but corruptible, has military escort and cargo inspection services
   - `jinshan_monk` (了凡禅师): Temple abbot with connections to Yangzhou's Fahai Temple, informant
   - `xijin_ferryman` (马渡子): Silent ferryman who observes all river traffic, has crossing and night crossing services

3. **Side thread** ("卫所扣货"):
   - Hook: Military garrison seized a shipment from Yangzhou suspected of containing smuggled salt
   - Anchors: Zhenjiang fortress, ferry, temple + merchant_wu
   - Stakes: Key evidence for the "江南暗网" investigation, but the military is dangerous to provoke

4. **Geographic connection**:
   - Guazhou ferry → Zhenjiang Xijin (south_zhenjiang exit)
   - Creates a logical travel path: Yangzhou → Guazhou (ferry) → Zhenjiang → Nanjing

## Consequences

- **Positive**: Adds a strategically important location that fills the gap between Guazhou and Nanjing. The military angle provides new investigation dimension (military cover for smuggling).
- **Positive**: Follows established pattern (3+3+1), maintaining consistency with other regions.
- **Positive**: The side thread connects to the existing "江南暗网" investigation, giving players another evidence source.
- **Neutral**: No changes to existing systems — pure content addition.
- **Risk**: Minimal — follows proven pattern, all tests pass.
