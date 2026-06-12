# ADR-0118: Phase 32 — Regional NPC Dialogue Lines

## Status

Accepted

## Context

Phase 28 introduced the NPC dialogue system (`get_npc_dialogue` / `record_dialogue`) and added `dialogue_lines` to 12 key Yangzhou-region NPCs. Phase 29 extended this to Xuzhou NPCs. However, 12 NPCs across 4 regional expansion files (Suzhou, Hangzhou, Huai'an, Zhenjiang) lacked `dialogue_lines`, creating an inconsistency: players visiting these regions would get generic dialogue behavior instead of personality-driven responses.

## Decision

Add `dialogue_lines` to all 12 remaining regional NPCs, following the same structure established in Phase 28:

- **greetings**: 3 attitude-tiered greetings (hostile/neutral/friendly)
- **topics**: 2 topics each with `unlock_attitude` thresholds and 2 attitude-tiered lines
- **farewells**: 2 attitude-tiered farewells
- **special**: `first_meeting` + `high_attitude` triggers

Each NPC's dialogue content reflects their occupation, personality, and connection to regional investigation threads (silk smuggling, tea transport, grain corruption, military seized cargo).

## Consequences

- **Positive**: All 57 NPCs now have consistent dialogue coverage. Players get personality-driven responses in every region.
- **Positive**: Dialogue topics reinforce regional investigation threads, giving players natural conversation leads.
- **Positive**: 12 new tests ensure dialogue structure integrity.
- **Neutral**: No new tools or API changes required — existing `get_npc_dialogue` handles the new data automatically.
