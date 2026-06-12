# ADR-0112: Phase 26 — Frontend Investigation Quest Panel

**Date**: 2026-06-12
**Status**: Accepted

## Context

Phase 23 added cross-region investigation mechanics with `quest_log` (via `update_quest_log` / `list_quest_log` tools) and cross-region clues. The data was available through the world snapshot (`flags.quest_log`) and the GM Agent could record milestones, but there was no frontend panel to display investigation progress to the player. The right sidebar had story, clues, and pressure panels, but no dedicated view for quest/investigation tracking.

## Decision

Add a "调查进度" (Investigation Progress) panel to the right sidebar showing:

1. **Overview bar**: Counts of active, completed, locked entries and number of regions explored.

2. **Region progress summary**: For each region with quest entries, show a progress bar (completed/total) sorted by completion percentage. Visual indicator of how far each region's investigation has progressed.

3. **Entry list**: Each quest entry showing status badge (进行中/已完成/未解锁), region tag, title, and description. Sorted: active first, then completed, then locked. Compact mode limits to 5 entries.

4. **Side nav badge**: "调查" navigation button with badge showing active and completed counts.

Panel placement: after "线索记录" and before "压力钟" in the sidebar order.

## Consequences

- Backend data already exists via `flags.quest_log` — no new API endpoints needed
- Panel integrates with existing collapsible, searchable, density-toggle infrastructure
- Region aggregation gives players a geographic overview of investigation coverage
- Status badges (active/completed/locked) provide at-a-glance progress tracking
- 1 new server test verifying quest_log data propagation through snapshot
