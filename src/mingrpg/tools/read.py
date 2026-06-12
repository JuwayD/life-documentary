"""Read tools — expose world state to the GM Agent.

Pure read-only functions. No state changes, no decision logic.
Each tool returns a JSON-serialisable dict. Errors are returned as
`{"error": "...", "suggestion": "..."}` rather than raised.
"""
import math
import os
from pathlib import Path

import yaml

from mingrpg.core.world import World
from mingrpg.retrieval import TfidfIndex


# ---------------------------------------------------------------------------
# Law data cache
# ---------------------------------------------------------------------------
_LAW_DIR = str(Path(__file__).parent.parent.parent.parent / "data" / "laws")
_LAWS_CACHE: list[dict] | None = None
_LAW_INDEX: TfidfIndex | None = None


def _reset_laws_cache():
    """Test helper to reset the laws cache after changing _LAW_DIR."""
    global _LAWS_CACHE, _LAW_INDEX
    _LAWS_CACHE = None
    _LAW_INDEX = None


def _load_laws() -> list[dict]:
    global _LAWS_CACHE
    if _LAWS_CACHE is not None:
        return _LAWS_CACHE
    laws: list[dict] = []
    if not os.path.isdir(_LAW_DIR):
        _LAWS_CACHE = laws
        return laws
    for fname in sorted(os.listdir(_LAW_DIR)):
        if not (fname.endswith(".yaml") or fname.endswith(".yml")):
            continue
        path = os.path.join(_LAW_DIR, fname)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []
            if isinstance(data, list):
                laws.extend(data)
    _LAWS_CACHE = laws
    return laws


def _get_law_index() -> TfidfIndex:
    """Build (or return cached) TF-IDF index over loaded laws."""
    global _LAW_INDEX
    if _LAW_INDEX is not None:
        return _LAW_INDEX
    laws = _load_laws()
    _LAW_INDEX = TfidfIndex(laws)
    return _LAW_INDEX


# ---------------------------------------------------------------------------
# Entity reads
# ---------------------------------------------------------------------------
def get_entity(world: World, entity_id: str) -> dict:
    """Read full state of an entity by id."""
    e = world.get_entity(entity_id)
    if e is None:
        return {
            "error": f"entity '{entity_id}' not found",
            "suggestion": "use list_entities_nearby to discover valid ids",
        }
    return e


def get_location(world: World, location_id: str) -> dict:
    """Read full state of a location by id."""
    loc = world.get_location(location_id)
    if loc is None:
        return {
            "error": f"location '{location_id}' not found",
            "suggestion": "check spelling or get_entity first to find current location",
        }
    return loc


def list_entities_nearby(world: World, actor_id: str,
                         radius: int = 5) -> dict:
    """List entities within `radius` (Chebyshev/Euclidean) of the actor.

    Filters by same location and excludes the actor itself.
    """
    actor = world.get_entity(actor_id)
    if actor is None:
        return {"error": f"actor '{actor_id}' not found",
                "suggestion": "verify actor id"}
    here = actor.get("location")
    ax, ay = actor.get("pos", [0, 0])
    out = []
    for e in world.list_entities_at(here):
        if e["id"] == actor_id:
            continue
        ex, ey = e.get("pos", [0, 0])
        dist = math.sqrt((ex - ax) ** 2 + (ey - ay) ** 2)
        if dist <= radius:
            out.append({**e, "_distance": round(dist, 2)})
    out.sort(key=lambda e: e["_distance"])
    return {"actor_position": [ax, ay], "radius": radius, "entities": out}


def get_world_time(world: World) -> dict:
    """Get current in-game time (year/season/time_of_day)."""
    return world.get_world_time()


def get_recent_events(world: World, limit: int = 10) -> dict:
    """Recent world events (append-only log)."""
    return {"events": world.list_events(limit=limit)}


# ---------------------------------------------------------------------------
# Location listing
# ---------------------------------------------------------------------------
def list_locations(world: World) -> dict:
    """List all locations in the world (id, name, type, exits, tags)."""
    return {"locations": world.list_locations()}


# ---------------------------------------------------------------------------
# Law queries
# ---------------------------------------------------------------------------
def query_laws(
    keywords: list[str] | None = None,
    query: str | None = None,
    top_k: int = 5,
) -> dict:
    """Search laws/customs by keyword overlap and/or semantic similarity.

    Supports three modes:
    - ``keywords`` only: classic keyword substring matching (backward compat).
    - ``query`` only: TF-IDF vector retrieval via jieba segmentation.
    - Both: results from both methods are merged, vector scores weighted higher.

    Returns up to ``top_k`` matching law entries, sorted by combined score.
    """
    laws = _load_laws()
    if not laws:
        return {"laws": [],
                "note": "no laws loaded; check data/laws/ directory"}

    # --- vector retrieval ---
    vector_results: dict[str, float] = {}
    if query and query.strip():
        index = _get_law_index()
        hits = index.query(query, top_k=top_k * 2)
        for hit in hits:
            vector_results[hit["id"]] = hit["_score"]

    # --- keyword retrieval ---
    keyword_results: dict[str, float] = {}
    if keywords:
        keywords_norm = [k.strip().lower() for k in keywords if k.strip()]
        for law in laws:
            kw = [str(k).lower() for k in law.get("keywords", [])]
            text = str(law.get("text", "")).lower()
            score = 0.0
            for q in keywords_norm:
                if any(q in k or k in q for k in kw):
                    score += 2
                if q in text:
                    score += 1
            if score > 0:
                keyword_results[law["id"]] = score

    # --- merge results ---
    if not vector_results and not keyword_results:
        return {"laws": [], "mode": "none"}

    # Determine mode label
    if vector_results and keyword_results:
        mode = "hybrid"
    elif vector_results:
        mode = "vector"
    else:
        mode = "keyword"

    # Build law lookup
    law_by_id = {law["id"]: law for law in laws}

    # Combine scores: vector scores are normalised 0-1, keyword scores are
    # integer multiples of 1.  Weight vector at 3x to give semantic meaning
    # priority while still rewarding exact keyword hits.
    all_ids = set(vector_results) | set(keyword_results)
    combined: list[tuple[float, str]] = []
    for lid in all_ids:
        vscore = vector_results.get(lid, 0.0) * 3.0
        kscore = keyword_results.get(lid, 0.0)
        combined.append((vscore + kscore, lid))
    combined.sort(key=lambda x: -x[0])

    result_laws = []
    for _, lid in combined[:top_k]:
        if lid in law_by_id:
            result_laws.append(law_by_id[lid])
    return {"laws": result_laws, "mode": mode}


def list_advisors(world: World, location_id: str | None = None) -> dict:
    """Return all NPCs marked as advisors, optionally filtered by location."""
    advisors = []
    for entity in world.list_entities():
        if not entity.get("attributes", {}).get("is_advisor"):
            continue
        if location_id is not None and entity.get("location") != location_id:
            continue
        advisors.append({
            "id": entity["id"],
            "name": entity["name"],
            "location": entity.get("location"),
            "rank": entity["attributes"].get("rank", ""),
            "occupation": entity["attributes"].get("occupation", ""),
            "advisor_topics": entity["attributes"].get("advisor_topics", []),
            "advisor_style": entity["attributes"].get("advisor_style", ""),
            "personality": entity["attributes"].get("personality", ""),
        })
    return {"advisors": advisors}


def list_party(world: World, leader_id: str = "player") -> dict:
    """Return the player's current party membership."""
    leader = world.get_entity(leader_id)
    if leader is None:
        return {"error": f"leader '{leader_id}' not found",
                "suggestion": "verify leader id with get_entity first"}

    party = world.get_flag("party") or {
        "leader_id": leader_id,
        "active_actor_id": leader_id,
        "members": [{"entity_id": leader_id, "role": "主角", "joined_reason": "初始队伍"}],
    }
    members = []
    for member in party.get("members", []):
        entity = world.get_entity(member.get("entity_id"))
        if entity is None:
            continue
        members.append({
            "id": entity["id"],
            "name": entity["name"],
            "type": entity.get("type"),
            "location": entity.get("location"),
            "pos": entity.get("pos", []),
            "rank": entity.get("attributes", {}).get("rank", ""),
            "occupation": entity.get("attributes", {}).get("occupation", ""),
            "personality": entity.get("attributes", {}).get("personality", ""),
            "role": member.get("role", ""),
            "joined_reason": member.get("joined_reason", ""),
            "is_active": entity["id"] == party.get("active_actor_id", leader_id),
        })
    return {"leader_id": party.get("leader_id", leader_id),
            "active_actor_id": party.get("active_actor_id", leader_id),
            "members": members}


def list_skills(world: World, entity_id: str = "player") -> dict:
    """List skills for an entity. Returns empty dict if no skills."""
    e = world.get_entity(entity_id)
    if e is None:
        return {"error": f"entity '{entity_id}' not found",
                "suggestion": "verify entity id with get_entity first"}
    skills = e.get("attributes", {}).get("skills", {})
    return {"entity_id": entity_id, "entity_name": e["name"], "skills": skills}


def list_endings(world: World) -> dict:
    """List available ending seeds, recorded ending progress, and step progress."""
    seeds = world.get_flag("ending_seeds") or []
    progress = world.get_flag("ending_progress") or {"endings": []}
    steps = world.get_flag("ending_steps") or {}
    return {"ending_seeds": seeds, "ending_progress": progress, "ending_steps": steps}


def list_quest_log(world: World, status: str | None = None) -> dict:
    """List quest log entries, optionally filtered by status.

    Returns investigation milestones and cross-region progress tracking.
    """
    quest_log = world.get_flag("quest_log") or {"entries": []}
    entries = quest_log.get("entries", [])
    if status is not None:
        entries = [e for e in entries if e.get("status") == status]
    active = sum(1 for e in quest_log.get("entries", [])
                 if e.get("status") == "active")
    completed = sum(1 for e in quest_log.get("entries", [])
                    if e.get("status") == "completed")
    locked = sum(1 for e in quest_log.get("entries", [])
                 if e.get("status") == "locked")
    return {"entries": entries, "total": len(quest_log.get("entries", [])),
            "active": active, "completed": completed, "locked": locked}


def list_evolutions(world: World) -> dict:
    """List all entities registered for world evolution."""
    registry = world.get_flag("evolution_registry") or []
    turn_index = world.get_flag("turn_index") or len(world.list_events(limit=10000))

    entries = []
    for entry in registry:
        entity = world.get_entity(entry["entity_id"])
        entries.append({
            "entity_id": entry["entity_id"],
            "entity_name": entity["name"] if entity else entry["entity_id"],
            "entity_location": entity.get("location") if entity else None,
            "frequency": entry["frequency"],
            "last_evolved_turn": entry.get("last_evolved_turn", 0),
            "turns_since_evolution": turn_index - entry.get("last_evolved_turn", 0),
            "reason": entry.get("reason", ""),
        })

    return {"evolutions": entries, "count": len(entries),
            "current_turn": turn_index}


def get_npc_dialogue(world: World, npc_id: str,
                     player_id: str = "player") -> dict:
    """Get available dialogue lines for an NPC based on attitude toward player.

    Returns greetings, available topics, farewells, and special triggers.
    Each line is filtered by the NPC's current attitude toward the player.
    """
    npc = world.get_entity(npc_id)
    if npc is None:
        return {"error": f"entity '{npc_id}' not found",
                "suggestion": "use list_entities_nearby to find NPCs"}
    if npc.get("type") != "npc":
        return {"error": f"'{npc.get('name', npc_id)}' is not an NPC",
                "suggestion": "dialogue only works with NPC entities"}

    player = world.get_entity(player_id)
    if player is None:
        return {"error": f"player '{player_id}' not found"}

    attitude = npc.get("attributes", {}).get("attitude", {}).get(player_id, 0)
    dialogue_lines = npc.get("attributes", {}).get("dialogue_lines", {})

    def in_range(line: dict) -> bool:
        lo = line.get("min_attitude", -100)
        hi = line.get("max_attitude", 100)
        return lo <= attitude <= hi

    # Filter greetings by attitude
    greetings = [g["text"] for g in dialogue_lines.get("greetings", [])
                 if in_range(g)]

    # Filter topics by unlock_attitude
    topics = []
    for t in dialogue_lines.get("topics", []):
        unlock = t.get("unlock_attitude", -100)
        if attitude < unlock:
            continue
        available_lines = [l["text"] for l in t.get("lines", []) if in_range(l)]
        if available_lines:
            topics.append({
                "id": t["id"],
                "label": t.get("label", t["id"]),
                "lines": available_lines,
            })

    # Filter farewells by attitude
    farewells = [f["text"] for f in dialogue_lines.get("farewells", [])
                 if in_range(f)]

    # Filter specials by trigger conditions
    specials = []
    for s in dialogue_lines.get("special", []):
        trigger = s.get("trigger", "")
        if trigger == "first_meeting":
            memories = npc.get("attributes", {}).get("memories", [])
            met_player = any("玩家" in m.get("text", "") or player_id in m.get("text", "")
                            for m in memories)
            if not met_player and in_range(s):
                specials.append({"trigger": trigger, "text": s["text"]})
        elif trigger == "high_attitude":
            if attitude >= s.get("min_attitude", 50) and in_range(s):
                specials.append({"trigger": trigger, "text": s["text"]})
        elif trigger == "low_attitude":
            if attitude <= s.get("max_attitude", -20) and in_range(s):
                specials.append({"trigger": trigger, "text": s["text"]})
        else:
            if in_range(s):
                specials.append({"trigger": trigger, "text": s["text"]})

    return {
        "npc_id": npc_id,
        "npc_name": npc["name"],
        "attitude": attitude,
        "greetings": greetings,
        "topics": topics,
        "farewells": farewells,
        "specials": specials,
    }


def get_weather(world: World) -> dict:
    """Get current weather conditions.

    Returns weather from world flag 'weather'. If not set, returns a
    default based on the current season.
    """
    weather = world.get_flag("weather")
    if weather is not None:
        return weather

    # Default weather based on season
    season = world.get_world_time().get("season", "秋")
    defaults = {
        "春": {"condition": "cloudy", "intensity": "light",
               "text": "春日阴云漫天,微风拂面,空气湿润。"},
        "夏": {"condition": "clear", "intensity": "moderate",
               "text": "盛夏烈日当空,暑气逼人,蝉鸣阵阵。"},
        "秋": {"condition": "clear", "intensity": "light",
               "text": "秋高气爽,天朗气清,正是出游好时节。"},
        "冬": {"condition": "cloudy", "intensity": "moderate",
               "text": "冬日铅云低垂,朔风凛冽,行人裹紧衣袍。"},
    }
    return defaults.get(season, defaults["秋"])


def list_observables(world: World, actor_id: str = "player",
                     include_discovered: bool = True) -> dict:
    """List currently visible observable details for an actor."""
    actor = world.get_entity(actor_id)
    if actor is None:
        return {"error": f"actor '{actor_id}' not found",
                "suggestion": "verify actor id with get_entity first"}

    location_id = actor.get("location")
    location = world.get_location(location_id)
    if location is None:
        return {"error": f"location '{location_id}' not found",
                "suggestion": "move actor to a valid location"}

    observation_score = actor.get("attributes", {}).get("observation", 10)
    discovered = (world.get_flag("observations") or {}).get(actor_id, {})
    details = []

    def add_details(target: dict, target_type: str):
        source = target.get("observable_details", [])
        if target_type == "entity":
            source = target.get("attributes", {}).get("observable_details", [])
        for detail in source:
            key = f"{target_type}:{target['id']}:{detail['id']}"
            is_discovered = key in discovered
            if detail.get("discovery_value", 0) <= observation_score or (
                    include_discovered and is_discovered):
                details.append({
                    **detail,
                    "target_id": target["id"],
                    "target_name": target.get("name", target["id"]),
                    "target_type": target_type,
                    "discovered": is_discovered,
                })

    add_details(location, "location")
    for entity in world.list_entities_at(location_id):
        if entity["id"] != actor_id:
            add_details(entity, "entity")

    details.sort(key=lambda d: (d.get("discovery_value", 0), d["target_type"], d["target_id"]))
    return {"actor_id": actor_id, "location_id": location_id,
            "observation_score": observation_score, "details": details}
