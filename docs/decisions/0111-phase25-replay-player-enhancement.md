# ADR-0111: Phase 25 — Replay Player Enhancement

**Date**: 2026-06-12
**Status**: Accepted

## Context

The replay player (Phase 14) provided basic playback controls (prev/next/slider/auto-play) but lacked visual context for navigating long play sessions. Players had no way to quickly identify turn types, see what changed between turns, or control playback speed.

## Decision

Enhance the replay player with three features:

1. **Visual Timeline Bar**: A horizontal bar of colored markers (one per turn) showing turn type at a glance. Colors: combat=red, social=blue, story=green, trade=yellow, other=gray. Clicking a marker jumps directly to that turn.

2. **Turn Diff Panel**: Below the narration, a compact panel showing state changes between consecutive turns — HP/money changes, location moves, status gains/losses, flag updates, new events, and new clues. Limited to 20 items with overflow indicator.

3. **Speed Control + Keyboard Shortcuts**: A dropdown to select playback speed (0.5x/1x/2x/4x). Keyboard shortcuts: Left/Right arrows for prev/next, Space for play/pause, Home/End for start/end.

All computation is frontend-only using the existing `replay_to_player_data` API which already returns full state snapshots at each turn.

## Consequences

- No backend changes required — all diff computation done client-side
- Timeline markers classify turns by examining write tool types
- Diff computation compares entity attributes, locations, statuses, flags, events, and clues
- Keyboard handler is properly cleaned up on modal close
- 4 new E2E tests covering timeline, speed control, diff panel, and keyboard hint
