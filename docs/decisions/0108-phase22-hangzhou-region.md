# ADR-0108: Phase 22 — New Region Hangzhou (杭州)

## Status

Accepted

## Context

Following the pattern established in Phase 17 (瓜洲渡), Phase 20 (南京), and Phase 21 (苏州), the project needs to expand the world with more江南 cities to increase narrative breadth and player exploration options. Hangzhou is the natural next step — it is the southern terminus of the Grand Canal, historically one of the most prosperous cities in明代, and culturally connected to both苏州 and扬州.

## Decision

Add杭州 as a new region with:

- **3 locations**: 西湖 (West Lake), 灵隐寺 (Lingyin Temple), 拱宸桥码头 (Gongchen Canal Dock)
- **3 NPCs**: 方掌柜 (tea merchant), 明空方丈 (temple abbot), 孙船老大 (canal captain)
- **1 side thread**: 龙井暗运 (Longjing tea smuggling) — links to扬州 merchant_wu and苏州 silk trade
- **Canal connection**: 苏州枫桥 ↔ 杭州拱宸桥码头 (bidirectional)

### Design rationale

- **西湖** is杭州's iconic landmark, providing scenic contrast to the urban扬州 and canal-focused苏州
- **灵隐寺** adds a religious/academic location, offering new interaction types (spiritual guidance, scholarly discourse)
- **拱宸桥码头** follows the established canal dock pattern for inter-region travel
- **方掌柜** as tea merchant parallels苏州's钱掌柜 (silk merchant), creating a trade network thread
- **明空方丈** as advisor-type NPC provides a non-commercial information source
- **孙船老大** as canal captain parallels苏州's冯船家 and瓜洲渡's陈老渡, maintaining the ferryman pattern
- **龙井暗运** side thread connects to existing扬州/苏州 storylines via merchant_wu's smuggling network

## Consequences

- 48 total entities (45 + 3), 35 total locations (32 + 3)
- GM system prompt updated with杭州 region and NPC descriptions
- Evolution registry populated for all 3 new NPCs
- Test suite: 21 new region tests, all passing
