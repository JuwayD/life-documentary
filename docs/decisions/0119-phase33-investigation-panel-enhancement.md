# ADR-0119: Phase 33 — Investigation Panel Enhancement

## Status

Accepted

## Context

The investigation panel (quest log) provides players with a way to track their progress across multiple regions. However, the current implementation has several limitations:

1. The quest timeline shows events in a flat list without filtering capabilities
2. The cross-region flow map only shows basic progress indicators
3. Players cannot easily filter investigation events by region or status
4. Clue counts are not visible in the region flow map

## Decision

Enhance the investigation panel with two main improvements:

### 1. Quest Timeline Filtering
- Add filter chips for region and status
- Show summary statistics (total events, most recent region)
- Add timestamp display for events
- Support dynamic filtering without page reload

### 2. Cross-Region Flow Map Enhancement
- Add clue count badges to each region node
- Add click-to-expand detail view for each region
- Show region-specific investigation entries in detail panel
- Add visual feedback for selected region node

## Implementation Details

### Frontend Changes
- `app.js`: Enhanced `renderQuestLogPanel()` with filter UI and flow map interactivity
- `style.css`: Added styles for filter chips, detail panel, and flow node states

### Data Structure
- Quest timeline events already include `region` and `status` fields
- Story progress data provides clue counts per region
- No backend API changes required

## Consequences

- **Positive**: Players can quickly filter investigation events by region or status
- **Positive**: Clue counts visible at a glance in the region flow map
- **Positive**: Click-to-expand provides detailed view without leaving the panel
- **Positive**: Visual feedback (selected state) improves interaction clarity
- **Neutral**: No new tools or API changes required
- **Neutral**: Existing data structures support the enhancement without modification
