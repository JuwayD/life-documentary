"""FastAPI web layer for mingrpg.

A thin transport wrapper around the existing GMAgent. No game logic here.
"""
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.world import World
from mingrpg.llm.agent import GMAgent
from mingrpg.tools.birth import apply_birth_template, get_birth_template, list_birth_templates
from mingrpg.scenarios.yangzhou_court import seed_yangzhou_court
from mingrpg.scenarios.yangzhou_market import seed_yangzhou_market
from mingrpg.scenarios.yangzhou_inn import seed_yangzhou_inn
from mingrpg.scenarios.yangzhou_districts import seed_yangzhou_districts
from mingrpg.scenarios.yangzhou_phase11 import seed_yangzhou_phase11
from mingrpg.scenarios.yangzhou_phase12 import seed_yangzhou_phase12
from mingrpg.scenarios.yangzhou_phase13 import seed_yangzhou_phase13
from mingrpg.scenarios.guazhou import seed_guazhou
from mingrpg.scenarios.nanjing import seed_nanjing
from mingrpg.scenarios.suzhou import seed_suzhou
from mingrpg.scenarios.hangzhou import seed_hangzhou
from mingrpg.scenarios.zhenjiang import seed_zhenjiang
from mingrpg.scenarios.phase23_main_story import seed_phase23_main_story


def seed_all(world: World) -> None:
    """Seed all scenarios into the world."""
    seed_yangzhou_court(world)
    seed_yangzhou_market(world)
    seed_yangzhou_inn(world)
    seed_yangzhou_districts(world)
    seed_yangzhou_phase11(world)
    seed_yangzhou_phase12(world)
    seed_yangzhou_phase13(world)
    seed_guazhou(world)
    seed_nanjing(world)
    seed_suzhou(world)
    seed_hangzhou(world)
    seed_zhenjiang(world)
    seed_phase23_main_story(world)

    # Seed initial weather based on season
    season = world.get_world_time().get("season", "秋")
    weather_defaults = {
        "春": {"condition": "cloudy", "intensity": "light",
               "text": "春日阴云漫天,微风拂面,空气湿润。"},
        "夏": {"condition": "clear", "intensity": "moderate",
               "text": "盛夏烈日当空,暑气逼人,蝉鸣阵阵。"},
        "秋": {"condition": "clear", "intensity": "light",
               "text": "秋高气爽,天朗气清,正是出游好时节。"},
        "冬": {"condition": "cloudy", "intensity": "moderate",
               "text": "冬日铅云低垂,朔风凛冽,行人裹紧衣袍。"},
    }
    if not world.get_flag("weather"):
        world.set_flag("weather", weather_defaults.get(season, weather_defaults["秋"]))


STATIC_DIR = Path(__file__).parent / "static"

# --- Default LLM config (matches CLI) ---
DEFAULT_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/anthropic"
DEFAULT_API_KEY = "tp-srtg3w0atiqiyhe84myptmcnc4xnyg6j0ej5vn8d0eoceswx"
DEFAULT_MODEL = "mimo-v2.5-pro"


class TurnRequest(BaseModel):
    input: str


class SaveImportRequest(BaseModel):
    save: dict


class BirthApplyRequest(BaseModel):
    template_id: str


class TestSnapshotCreateRequest(BaseModel):
    name: str
    note: str = ""
    tags: list[str] = []


class TestSnapshotUpdateRequest(BaseModel):
    name: str | None = None
    note: str | None = None
    tags: list[str] | None = None
    pinned: bool | None = None
    archived: bool | None = None


class TestSnapshotLoadRequest(BaseModel):
    snapshot_id: str


class TestSnapshotImportRequest(BaseModel):
    snapshot: dict


class TestSnapshotBulkDeleteRequest(BaseModel):
    snapshot_ids: list[str]


class TestSnapshotBulkExportRequest(BaseModel):
    snapshot_ids: list[str]


class TestSnapshotBulkArchiveRequest(BaseModel):
    snapshot_ids: list[str]
    archived: bool = True


class TestSnapshotBulkImportRequest(BaseModel):
    bundle: dict


class TestSnapshotDuplicateRequest(BaseModel):
    name: str | None = None
    note: str | None = None
    tags: list[str] | None = None
    pinned: bool | None = None


class TestPresetLoadRequest(BaseModel):
    preset_id: str


def _default_agent_factory(world, audit, **kw):
    return GMAgent(
        world=world,
        audit=audit,
        model=os.environ.get("MINGRPG_MODEL", DEFAULT_MODEL),
        api_key=os.environ.get("MINGRPG_API_KEY", DEFAULT_API_KEY),
        base_url=os.environ.get("MINGRPG_BASE_URL", DEFAULT_BASE_URL),
    )


def create_app(agent_factory: Callable = _default_agent_factory,
               audit_dir: Path | str | None = None,
               db_path: str = ":memory:",
               seed_func: Callable = seed_all) -> FastAPI:
    """App factory — accepts an agent_factory for testing."""
    app = FastAPI(title="mingrpg")

    audit_dir = Path(audit_dir) if audit_dir else Path("runtime")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "audit.jsonl"
    test_snapshots_dir = audit_dir / "test_snapshots"
    test_snapshots_dir.mkdir(parents=True, exist_ok=True)
    app.state.test_snapshots_dir = test_snapshots_dir

    # ---- session-scoped (singleton for now) state ----
    state = {
        "world": None,
        "audit": None,
        "agent": None,
        "audit_path": audit_path,
        "db_path": db_path,
    }

    def _build():
        world = World(state["db_path"])
        seed_func(world)
        audit = AuditLogger(state["audit_path"])
        agent = agent_factory(world=world, audit=audit)
        state["world"] = world
        state["audit"] = audit
        state["agent"] = agent
        app.state.world = world

    _build()

    # -----------------------------------------------------------------
    # Static / Index
    # -----------------------------------------------------------------
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        index_html = STATIC_DIR / "index.html"
        if index_html.exists():
            return HTMLResponse(index_html.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>人生纪实</h1><p>前端尚未构建</p>")

    # -----------------------------------------------------------------
    # API
    # -----------------------------------------------------------------
    @app.get("/api/state")
    async def get_state():
        return state["world"].snapshot()

    @app.get("/api/birth/templates")
    async def get_birth_templates():
        return list_birth_templates()

    @app.get("/api/birth/templates/{template_id}")
    async def get_birth_template_detail(template_id: str):
        result = get_birth_template(template_id)
        if "error" in result:
            raise HTTPException(404, result["error"])
        return result

    @app.post("/api/birth/apply")
    async def post_birth_apply(req: BirthApplyRequest):
        result = apply_birth_template(state["world"], req.template_id)
        if "error" in result:
            raise HTTPException(404, result["error"])
        return {"ok": True, "result": result, "state": state["world"].snapshot()}

    @app.post("/api/turn")
    async def post_turn(req: TurnRequest):
        text = (req.input or "").strip()
        if not text:
            raise HTTPException(400, "input cannot be empty")
        narration = state["agent"].process_input(text)
        return {
            "input": text,
            "narration": narration,
            "state": state["world"].snapshot(),
        }

    @app.websocket("/ws/turn")
    async def ws_turn(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                raw = await ws.receive_text()
                data = json.loads(raw)
                text = (data.get("input", "") or "").strip()
                if not text:
                    await ws.send_json({"type": "error", "message": "input cannot be empty"})
                    continue
                for event in state["agent"].process_input_stream(text):
                    await ws.send_json(event)
                # send latest snapshot for side panel update
                await ws.send_json({
                    "type": "state",
                    "state": state["world"].snapshot(),
                })
        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await ws.send_json({"type": "error", "message": str(e)})
            except Exception:
                pass

    def _read_audit_turns(limit: int | None = None, offset: int = 0) -> tuple[list[dict], int]:
        path = state["audit_path"]
        if not path.exists():
            return [], 0
        lines = [line for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]
        total = len(lines)
        turns = [json.loads(line) for line in lines]
        if offset > 0:
            turns = turns[:-offset] if offset < len(turns) else []
        if limit is not None:
            turns = turns[-limit:]
        return turns, total

    @app.get("/api/audit")
    async def get_audit(limit: int = 50, offset: int = 0):
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        turns, total = _read_audit_turns(limit, offset)
        has_more = offset + limit < total
        return {"turns": turns, "total": total, "offset": offset, "has_more": has_more}

    def _debug_console_payload(limit: int = 20, tool: str | None = None, q: str | None = None) -> dict:
        limit = max(1, min(limit, 500))
        tool_filter = (tool or "").strip()
        query = (q or "").strip().lower()
        snapshot = state["world"].snapshot()
        turns, total_turns = _read_audit_turns(limit)
        tool_calls = []
        for turn in turns:
            for step in turn.get("agent_trace", []):
                if step.get("type") == "tool_use":
                    tool_calls.append({
                        "turn": turn.get("turn"),
                        "name": step.get("name"),
                        "input": step.get("input"),
                        "output": step.get("output"),
                    })
        tool_names = sorted({call.get("name") for call in tool_calls if call.get("name")})
        if tool_filter:
            tool_calls = [call for call in tool_calls if call.get("name") == tool_filter]
        if query:
            tool_calls = [
                call for call in tool_calls
                if query in json.dumps(call, ensure_ascii=False).lower()
            ]
        filtered_tool_count = len(tool_calls)
        player = next((e for e in snapshot.get("entities", []) if e.get("id") == "player"), None)
        current_location = None
        if player:
            current_location = next(
                (l for l in snapshot.get("locations", []) if l.get("id") == player.get("location")),
                None,
            )
        return {
            "world": {
                "entity_count": len(snapshot.get("entities", [])),
                "location_count": len(snapshot.get("locations", [])),
                "event_count": len(snapshot.get("events", [])),
                "flag_count": len(snapshot.get("flags", {})),
                "time": snapshot.get("time", {}),
                "player": player,
                "current_location": current_location,
                "entities": snapshot.get("entities", []),
                "flags": snapshot.get("flags", {}),
            },
            "audit": {
                "turn_count": total_turns,
                "recent_tool_calls": tool_calls[-limit:],
                "tool_names": tool_names,
                "tool_filter": tool_filter,
                "query": query,
                "filtered_tool_count": filtered_tool_count,
            },
            "performance": {
                "audit_bytes": state["audit_path"].stat().st_size if state["audit_path"].exists() else 0,
                "snapshot_event_window": len(snapshot.get("events", [])),
            },
        }

    @app.get("/api/debug/console")
    async def get_debug_console(limit: int = 20, tool: str | None = None, q: str | None = None):
        return _debug_console_payload(limit, tool, q)

    @app.get("/api/debug/export")
    async def export_debug_bundle(limit: int = 20, tool: str | None = None, q: str | None = None):
        payload = _debug_console_payload(limit, tool, q)
        payload["exported_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        payload["format"] = "mingrpg.debug-bundle"
        payload["version"] = 1
        return payload

    @app.get("/api/save")
    async def export_save():
        return state["world"].export_save()

    @app.post("/api/save/import")
    async def import_save(req: SaveImportRequest):
        try:
            state["world"].import_save(req.save)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True, "state": state["world"].snapshot()}

    @app.get("/api/save/replay")
    async def export_replay():
        return state["world"].export_replay_log(str(state["audit_path"]))

    @app.get("/api/save/replay/player")
    async def replay_player_data():
        from mingrpg.core.replay import replay_to_player_data
        replay_data = state["world"].export_replay_log(str(state["audit_path"]))
        try:
            return replay_to_player_data(replay_data)
        except ValueError as e:
            raise HTTPException(400, str(e))

    class ReplayImportRequest(BaseModel):
        replay: dict

    @app.post("/api/save/replay/import")
    async def import_replay(req: ReplayImportRequest):
        try:
            state["world"].import_replay_log(req.replay)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"ok": True, "state": state["world"].snapshot()}

    def _snapshot_path(snapshot_id: str) -> Path:
        if not snapshot_id or any(ch in snapshot_id for ch in "/\\"):
            raise HTTPException(400, "invalid snapshot id")
        return test_snapshots_dir / f"{snapshot_id}.json"

    def _read_test_snapshot(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(500, "corrupt test snapshot")

    def _normalize_snapshot_tags(tags: list[str] | None) -> list[str]:
        normalized = []
        seen = set()
        for raw_tag in tags or []:
            tag = str(raw_tag).strip()
            if tag and tag not in seen:
                normalized.append(tag)
                seen.add(tag)
        return normalized

    def _snapshot_meta(data: dict, keys: list[str] | None = None) -> dict:
        meta_keys = keys or ["id", "name", "note", "tags", "pinned", "archived", "created_at", "updated_at", "last_loaded_at", "last_exported_at", "last_imported_at"]
        meta = {key: data.get(key, "") for key in meta_keys}
        if "tags" in meta_keys:
            meta["tags"] = _normalize_snapshot_tags(data.get("tags", []))
        if "pinned" in meta_keys:
            meta["pinned"] = bool(data.get("pinned", False))
        if "archived" in meta_keys:
            meta["archived"] = bool(data.get("archived", False))
        return meta

    def _stable_json(value) -> str:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)

    def _diff_record_lists(current: list[dict], target: list[dict], key: str) -> dict:
        current_by_key = {item.get(key): item for item in current if item.get(key)}
        target_by_key = {item.get(key): item for item in target if item.get(key)}
        added = sorted(set(target_by_key) - set(current_by_key))
        removed = sorted(set(current_by_key) - set(target_by_key))
        changed = sorted(
            item_key for item_key in set(current_by_key) & set(target_by_key)
            if _stable_json(current_by_key[item_key]) != _stable_json(target_by_key[item_key])
        )
        return {"added": added, "removed": removed, "changed": changed}

    def _diff_flags(current: dict, target: dict) -> dict:
        current_keys = set(current)
        target_keys = set(target)
        changed = sorted(
            key for key in current_keys & target_keys
            if _stable_json(current[key]) != _stable_json(target[key])
        )
        return {
            "added": sorted(target_keys - current_keys),
            "removed": sorted(current_keys - target_keys),
            "changed": changed,
        }

    def _debug_snapshot_diff(snapshot_data: dict) -> dict:
        current = state["world"].export_save().get("world", {})
        target = snapshot_data.get("save", {}).get("world", {})
        entities = _diff_record_lists(current.get("entities", []), target.get("entities", []), "id")
        locations = _diff_record_lists(current.get("locations", []), target.get("locations", []), "id")
        flags = _diff_flags(current.get("flags", {}), target.get("flags", {}))
        events_changed = _stable_json(current.get("events", [])) != _stable_json(target.get("events", []))
        time_changed = _stable_json(current.get("time", {})) != _stable_json(target.get("time", {}))
        total_changes = sum(
            len(section[change_type])
            for section in [entities, locations, flags]
            for change_type in ["added", "removed", "changed"]
        ) + int(events_changed) + int(time_changed)
        return {
            "snapshot": {k: snapshot_data.get(k, "") for k in ["id", "name", "note", "created_at"]},
            "summary": {
                "total_changes": total_changes,
                "events_changed": events_changed,
                "time_changed": time_changed,
            },
            "current_counts": {
                "entities": len(current.get("entities", [])),
                "locations": len(current.get("locations", [])),
                "events": len(current.get("events", [])),
                "flags": len(current.get("flags", {})),
            },
            "snapshot_counts": {
                "entities": len(target.get("entities", [])),
                "locations": len(target.get("locations", [])),
                "events": len(target.get("events", [])),
                "flags": len(target.get("flags", {})),
            },
            "entities": entities,
            "locations": locations,
            "flags": flags,
        }

    def _debug_test_presets() -> list[dict]:
        return [
            {
                "id": "court_clue_pressure",
                "name": "府衙线索压力局",
                "summary": "已有关键线索和证人压力,用于验证剧情、压力钟与时间线面板。",
                "actions": [
                    "记录状纸被师爷压下的关键线索",
                    "记录王知府催促结案的压力",
                ],
                "apply": lambda world: (
                    world.set_flag("story_progress", {
                        "main_thread": {
                            "clues": [{
                                "clue": "状纸曾被刘师爷压下,未及时呈给王知府",
                                "source_entity": "shiye",
                                "location_id": "court_hall",
                                "evidence_item": "petition_scroll",
                            }],
                        },
                    }),
                    world.set_flag("pressure_clocks", {
                        "witness_pressure": {"value": 2, "danger_at": 3},
                    }),
                    world.append_event({
                        "actor": "shiye",
                        "type": "record_clue",
                        "thread_id": "main_thread",
                        "summary": "预设: 状纸曾被刘师爷压下",
                        "clue": "状纸曾被刘师爷压下,未及时呈给王知府",
                        "source_entity": "shiye",
                        "location_id": "court_hall",
                    }),
                    world.append_event({
                        "actor": "system",
                        "type": "pressure_clock",
                        "clock_id": "witness_pressure",
                        "summary": "预设: 证人压力推进到2/3",
                        "old_value": 0,
                        "new_value": 2,
                        "danger_at": 3,
                        "danger_reached": False,
                        "reason": "测试预设",
                    }),
                ),
            },
            {
                "id": "advisor_party_observation",
                "name": "顾问同行观察局",
                "summary": "刘师爷已入队并发现公案桌细节,用于验证队伍、顾问、观察和关系动态。",
                "actions": [
                    "刘师爷加入队伍并成为当前行动角色",
                    "玩家发现公案桌上的可疑细节",
                ],
                "apply": lambda world: (
                    world.set_flag("party", {
                        "leader_id": "player",
                        "active_actor_id": "shiye",
                        "members": [
                            {"entity_id": "player", "role": "主角", "joined_reason": "初始队伍"},
                            {"entity_id": "shiye", "role": "府衙向导", "joined_reason": "测试预设同行"},
                        ],
                    }),
                    world.set_flag("observations", {
                        "player": {
                            "location:court_hall:court_hall_case_table": {
                                "detail_id": "court_hall_case_table",
                                "target_id": "court_hall",
                                "target_name": "扬州府衙大堂",
                                "target_type": "location",
                                "text": "公案上压着几份未批的状纸,其中一角露出血指印。",
                                "discovery_value": 8,
                                "source": "test_preset",
                            },
                        },
                    }),
                    world.append_event({
                        "actor": "shiye",
                        "type": "join_party",
                        "leader_id": "player",
                        "summary": "预设: 刘师爷加入无名书生的队伍",
                        "role": "府衙向导",
                        "joined_reason": "测试预设同行",
                    }),
                    world.append_event({
                        "actor": "player",
                        "type": "discover_observation",
                        "target": "court_hall",
                        "detail_id": "court_hall_case_table",
                        "summary": "预设: 无名书生发现公案桌上的血指印状纸",
                        "source": "test_preset",
                    }),
                ),
            },
        ]

    def _test_preset_summary(preset: dict) -> dict:
        return {k: preset[k] for k in ["id", "name", "summary", "actions"]}

    @app.get("/api/debug/test-presets")
    async def list_test_presets():
        return {"presets": [_test_preset_summary(preset) for preset in _debug_test_presets()]}

    @app.post("/api/debug/test-presets/load")
    async def load_test_preset(req: TestPresetLoadRequest):
        preset = next((p for p in _debug_test_presets() if p["id"] == req.preset_id), None)
        if preset is None:
            raise HTTPException(404, "test preset not found")
        _build()
        preset["apply"](state["world"])
        state["world"].set_flag("test_preset", _test_preset_summary(preset))
        return {"ok": True, "preset": _test_preset_summary(preset), "state": state["world"].snapshot()}

    def _list_test_snapshots() -> list[dict]:
        snapshots = []
        for path in test_snapshots_dir.glob("*.json"):
            data = _read_test_snapshot(path)
            save = data.get("save", {})
            world = save.get("world", {})
            snapshots.append({
                "id": data.get("id") or path.stem,
                "name": data.get("name") or path.stem,
                "note": data.get("note", ""),
                "tags": _normalize_snapshot_tags(data.get("tags", [])),
                "pinned": bool(data.get("pinned", False)),
                "archived": bool(data.get("archived", False)),
                "created_at": data.get("created_at", ""),
                "updated_at": data.get("updated_at", ""),
                "last_loaded_at": data.get("last_loaded_at", ""),
                "last_exported_at": data.get("last_exported_at", ""),
                "last_imported_at": data.get("last_imported_at", ""),
                "entity_count": len(world.get("entities", [])),
                "location_count": len(world.get("locations", [])),
                "event_count": len(world.get("events", [])),
                "flag_count": len(world.get("flags", {})),
            })
        pinned = [snapshot for snapshot in snapshots if snapshot["pinned"]]
        unpinned = [snapshot for snapshot in snapshots if not snapshot["pinned"]]
        pinned.sort(key=lambda snapshot: snapshot.get("updated_at") or snapshot.get("created_at") or "", reverse=True)
        unpinned.sort(key=lambda snapshot: snapshot.get("updated_at") or snapshot.get("created_at") or "", reverse=True)
        return pinned + unpinned

    def _test_snapshot_list_summary(snapshots: list[dict]) -> dict:
        latest_updated_at = max(
            (snapshot.get("updated_at") or snapshot.get("created_at") or "" for snapshot in snapshots),
            default="",
        )
        return {
            "snapshot_count": len(snapshots),
            "latest_updated_at": latest_updated_at,
            "totals": {
                "entities": sum(snapshot["entity_count"] for snapshot in snapshots),
                "locations": sum(snapshot["location_count"] for snapshot in snapshots),
                "events": sum(snapshot["event_count"] for snapshot in snapshots),
                "flags": sum(snapshot["flag_count"] for snapshot in snapshots),
            },
        }

    @app.get("/api/debug/test-snapshots")
    async def list_test_snapshots():
        snapshots = _list_test_snapshots()
        return {"snapshots": snapshots, "summary": _test_snapshot_list_summary(snapshots)}

    @app.get("/api/debug/test-snapshots/export-index")
    async def export_test_snapshot_index():
        snapshots = _list_test_snapshots()
        summary = _test_snapshot_list_summary(snapshots)
        return {
            "format": "mingrpg.test-snapshot-index",
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "snapshot_count": summary["snapshot_count"],
            "latest_updated_at": summary["latest_updated_at"],
            "totals": summary["totals"],
            "snapshots": snapshots,
        }

    def _validate_test_snapshot_health(data: dict, fallback_id: str, name_counts: dict[str, int]) -> dict:
        snapshot_id = data.get("id") or fallback_id
        name = data.get("name") or fallback_id
        issues = []
        if not data.get("id"):
            issues.append("missing_id")
        if not data.get("name"):
            issues.append("missing_name")
        if name_counts.get(name, 0) > 1:
            issues.append("duplicate_name")
        try:
            _validate_test_snapshot_payload({**data, "format": "mingrpg.test-snapshot", "version": 1})
        except HTTPException as e:
            issues.append(str(e.detail))
        world = data.get("save", {}).get("world", {}) if isinstance(data.get("save"), dict) else {}
        if not any(entity.get("id") == "player" for entity in world.get("entities", [])):
            issues.append("missing_player")
        if not world.get("locations"):
            issues.append("missing_locations")
        return {
            "id": snapshot_id,
            "name": name,
            "issues": issues,
            "ok": not issues,
        }

    def _test_snapshot_health_report() -> dict:
        valid_snapshots = []
        corrupt_snapshots = []
        for path in test_snapshots_dir.glob("*.json"):
            try:
                valid_snapshots.append((path, _read_test_snapshot(path)))
            except HTTPException as e:
                corrupt_snapshots.append({
                    "id": path.stem,
                    "name": path.stem,
                    "issues": [str(e.detail)],
                    "ok": False,
                })
        name_counts = {}
        for _, data in valid_snapshots:
            name = data.get("name") or data.get("id") or ""
            name_counts[name] = name_counts.get(name, 0) + 1
        checked = [
            _validate_test_snapshot_health(data, path.stem, name_counts)
            for path, data in valid_snapshots
        ] + corrupt_snapshots
        issues = [snapshot for snapshot in checked if not snapshot["ok"]]
        return {
            "snapshot_count": len(checked),
            "ok_count": len(checked) - len(issues),
            "issue_count": len(issues),
            "issues": issues,
        }

    @app.get("/api/debug/test-snapshots/health")
    async def check_test_snapshot_health():
        return _test_snapshot_health_report()

    @app.get("/api/debug/test-snapshots/health/export")
    async def export_test_snapshot_health():
        report = _test_snapshot_health_report()
        report.update({
            "format": "mingrpg.test-snapshot-health",
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        })
        return report

    @app.post("/api/debug/test-snapshots")
    async def create_test_snapshot(req: TestSnapshotCreateRequest):
        name = req.name.strip()
        if not name:
            raise HTTPException(400, "snapshot name cannot be empty")
        snapshot_id = uuid4().hex[:12]
        data = {
            "id": snapshot_id,
            "name": name,
            "note": req.note.strip(),
            "tags": _normalize_snapshot_tags(req.tags),
            "pinned": False,
            "archived": False,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "save": state["world"].export_save(),
        }
        _snapshot_path(snapshot_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "snapshot": _snapshot_meta(data)}

    @app.patch("/api/debug/test-snapshots/{snapshot_id}")
    async def update_test_snapshot(snapshot_id: str, req: TestSnapshotUpdateRequest):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        data = _read_test_snapshot(path)
        if req.name is not None:
            name = req.name.strip()
            if not name:
                raise HTTPException(400, "snapshot name cannot be empty")
            data["name"] = name
        if req.note is not None:
            data["note"] = req.note.strip()
        if req.tags is not None:
            data["tags"] = _normalize_snapshot_tags(req.tags)
        if req.pinned is not None:
            data["pinned"] = req.pinned
        if req.archived is not None:
            data["archived"] = req.archived
        data["updated_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "snapshot": _snapshot_meta(data)}

    @app.get("/api/debug/test-snapshots/{snapshot_id}")
    async def get_test_snapshot_detail(snapshot_id: str):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        data = _read_test_snapshot(path)
        world = data.get("save", {}).get("world", {})
        player = next((e for e in world.get("entities", []) if e.get("id") == "player"), None)
        current_location = None
        if player:
            current_location = next(
                (loc for loc in world.get("locations", []) if loc.get("id") == player.get("location")),
                None,
            )
        return {"snapshot": {
            "id": data.get("id") or snapshot_id,
            "name": data.get("name") or snapshot_id,
            "note": data.get("note", ""),
            "tags": _normalize_snapshot_tags(data.get("tags", [])),
            "pinned": bool(data.get("pinned", False)),
            "archived": bool(data.get("archived", False)),
            "created_at": data.get("created_at", ""),
            "updated_at": data.get("updated_at", ""),
            "last_loaded_at": data.get("last_loaded_at", ""),
            "last_exported_at": data.get("last_exported_at", ""),
            "entity_count": len(world.get("entities", [])),
            "location_count": len(world.get("locations", [])),
            "event_count": len(world.get("events", [])),
            "flag_count": len(world.get("flags", {})),
            "flag_keys": sorted(world.get("flags", {}).keys()),
            "player": player,
            "current_location": current_location,
            "recent_events": world.get("events", [])[-5:],
        }}

    def _validate_test_snapshot_payload(snapshot: dict) -> None:
        if snapshot.get("format") != "mingrpg.test-snapshot":
            raise HTTPException(400, "unsupported test snapshot format")
        if snapshot.get("version") != 1:
            raise HTTPException(400, "unsupported test snapshot version")
        save = snapshot.get("save")
        if not isinstance(save, dict):
            raise HTTPException(400, "missing test snapshot save")
        if save.get("format") != "mingrpg.save":
            raise HTTPException(400, "unsupported save format")
        if save.get("version") != 1:
            raise HTTPException(400, "unsupported save version")
        if not isinstance(save.get("world"), dict):
            raise HTTPException(400, "missing world data")

    def _validate_imported_test_snapshot(snapshot: dict) -> dict:
        _validate_test_snapshot_payload(snapshot)
        save = snapshot["save"]
        try:
            state["world"].import_save(save)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return save

    @app.get("/api/debug/test-snapshots/{snapshot_id}/export")
    async def export_test_snapshot(snapshot_id: str):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        data = _read_test_snapshot(path)
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        data["last_exported_at"] = now
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        exported = dict(data)
        exported["format"] = "mingrpg.test-snapshot"
        exported["version"] = 1
        exported["exported_at"] = now
        return exported

    @app.post("/api/debug/test-snapshots/{snapshot_id}/duplicate")
    async def duplicate_test_snapshot(snapshot_id: str, req: TestSnapshotDuplicateRequest):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        source = _read_test_snapshot(path)
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        name = req.name.strip() if req.name is not None else f"{source.get('name') or snapshot_id} 副本"
        if not name:
            raise HTTPException(400, "snapshot name cannot be empty")
        snapshot_id_new = uuid4().hex[:12]
        data = {
            "id": snapshot_id_new,
            "name": name,
            "note": req.note.strip() if req.note is not None else source.get("note", ""),
            "tags": _normalize_snapshot_tags(req.tags if req.tags is not None else source.get("tags", [])),
            "pinned": bool(req.pinned if req.pinned is not None else source.get("pinned", False)),
            "archived": bool(source.get("archived", False)),
            "created_at": now,
            "updated_at": now,
            "duplicated_from": source.get("id") or snapshot_id,
            "save": source.get("save", {}),
        }
        _snapshot_path(snapshot_id_new).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "snapshot": _snapshot_meta(data, ["id", "name", "note", "tags", "pinned", "archived", "created_at", "updated_at", "duplicated_from"])}

    @app.post("/api/debug/test-snapshots/import")
    async def import_test_snapshot(req: TestSnapshotImportRequest):
        snapshot = req.snapshot
        _validate_imported_test_snapshot(snapshot)
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        imported = {
            "id": snapshot.get("id") or "imported",
            "name": snapshot.get("name") or "导入测试快照",
            "note": snapshot.get("note", ""),
            "tags": _normalize_snapshot_tags(snapshot.get("tags", [])),
            "pinned": bool(snapshot.get("pinned", False)),
            "archived": bool(snapshot.get("archived", False)),
            "created_at": snapshot.get("created_at", ""),
            "last_imported_at": now,
        }
        return {"ok": True, "snapshot": imported, "state": state["world"].snapshot()}

    def _dedupe_snapshot_ids(raw_snapshot_ids: list[str]) -> list[str]:
        snapshot_ids = []
        seen = set()
        for snapshot_id in raw_snapshot_ids:
            if snapshot_id not in seen:
                snapshot_ids.append(snapshot_id)
                seen.add(snapshot_id)
        if not snapshot_ids:
            raise HTTPException(400, "snapshot ids cannot be empty")
        return snapshot_ids

    @app.post("/api/debug/test-snapshots/bulk-export")
    async def bulk_export_test_snapshots(req: TestSnapshotBulkExportRequest):
        snapshot_ids = _dedupe_snapshot_ids(req.snapshot_ids)
        exported_snapshots = []
        for snapshot_id in snapshot_ids:
            path = _snapshot_path(snapshot_id)
            if not path.exists():
                raise HTTPException(404, "test snapshot not found")
            data = _read_test_snapshot(path)
            exported = dict(data)
            exported["format"] = "mingrpg.test-snapshot"
            exported["version"] = 1
            exported_snapshots.append(exported)
        return {
            "format": "mingrpg.test-snapshot-bundle",
            "version": 1,
            "exported_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "snapshot_count": len(exported_snapshots),
            "snapshots": exported_snapshots,
        }

    def _validate_test_snapshot_bundle(bundle: dict) -> list[dict]:
        if bundle.get("format") != "mingrpg.test-snapshot-bundle":
            raise HTTPException(400, "unsupported test snapshot bundle format")
        if bundle.get("version") != 1:
            raise HTTPException(400, "unsupported test snapshot bundle version")
        bundle_snapshots = bundle.get("snapshots")
        if not isinstance(bundle_snapshots, list) or not bundle_snapshots:
            raise HTTPException(400, "snapshot bundle cannot be empty")
        for snapshot in bundle_snapshots:
            _validate_test_snapshot_payload(snapshot)
        return bundle_snapshots

    def _import_bundle_preview(bundle_snapshots: list[dict]) -> dict:
        snapshots = []
        for snapshot in bundle_snapshots:
            world = snapshot.get("save", {}).get("world", {})
            snapshots.append({
                "id": snapshot.get("id", ""),
                "name": snapshot.get("name") or snapshot.get("id") or "导入测试快照",
                "note": snapshot.get("note", ""),
                "tags": _normalize_snapshot_tags(snapshot.get("tags", [])),
                "pinned": bool(snapshot.get("pinned", False)),
                "archived": bool(snapshot.get("archived", False)),
                "created_at": snapshot.get("created_at", ""),
                "entity_count": len(world.get("entities", [])),
                "location_count": len(world.get("locations", [])),
                "event_count": len(world.get("events", [])),
                "flag_count": len(world.get("flags", {})),
            })
        return {
            "snapshot_count": len(snapshots),
            "totals": {
                "entities": sum(snapshot["entity_count"] for snapshot in snapshots),
                "locations": sum(snapshot["location_count"] for snapshot in snapshots),
                "events": sum(snapshot["event_count"] for snapshot in snapshots),
                "flags": sum(snapshot["flag_count"] for snapshot in snapshots),
            },
            "snapshots": snapshots,
        }

    @app.post("/api/debug/test-snapshots/bulk-import/preview")
    async def preview_bulk_import_test_snapshots(req: TestSnapshotBulkImportRequest):
        bundle_snapshots = _validate_test_snapshot_bundle(req.bundle)
        return _import_bundle_preview(bundle_snapshots)

    @app.post("/api/debug/test-snapshots/bulk-import")
    async def bulk_import_test_snapshots(req: TestSnapshotBulkImportRequest):
        bundle_snapshots = _validate_test_snapshot_bundle(req.bundle)
        imported = []
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        for snapshot in bundle_snapshots:
            snapshot_id = uuid4().hex[:12]
            data = {
                "id": snapshot_id,
                "name": snapshot.get("name") or "导入测试快照",
                "note": snapshot.get("note", ""),
                "tags": _normalize_snapshot_tags(snapshot.get("tags", [])),
                "pinned": bool(snapshot.get("pinned", False)),
                "archived": bool(snapshot.get("archived", False)),
                "created_at": now,
                "updated_at": now,
                "last_imported_at": now,
                "save": snapshot["save"],
            }
            _snapshot_path(snapshot_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            imported.append(_snapshot_meta(data))
        snapshots = _list_test_snapshots()
        return {"ok": True, "imported": imported, "summary": _test_snapshot_list_summary(snapshots)}

    @app.post("/api/debug/test-snapshots/bulk-archive")
    async def bulk_archive_test_snapshots(req: TestSnapshotBulkArchiveRequest):
        snapshot_ids = _dedupe_snapshot_ids(req.snapshot_ids)
        archived = []
        now = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        for snapshot_id in snapshot_ids:
            path = _snapshot_path(snapshot_id)
            if not path.exists():
                raise HTTPException(404, "test snapshot not found")
            data = _read_test_snapshot(path)
            data["archived"] = req.archived
            data["updated_at"] = now
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            archived.append(_snapshot_meta(data))
        snapshots = _list_test_snapshots()
        return {"ok": True, "archived": archived, "summary": _test_snapshot_list_summary(snapshots)}

    @app.post("/api/debug/test-snapshots/bulk-delete")
    async def bulk_delete_test_snapshots(req: TestSnapshotBulkDeleteRequest):
        snapshot_ids = _dedupe_snapshot_ids(req.snapshot_ids)
        deleted = []
        for snapshot_id in snapshot_ids:
            path = _snapshot_path(snapshot_id)
            if not path.exists():
                raise HTTPException(404, "test snapshot not found")
            data = _read_test_snapshot(path)
            path.unlink()
            deleted.append(_snapshot_meta(data))
        snapshots = _list_test_snapshots()
        return {"ok": True, "deleted": deleted, "summary": _test_snapshot_list_summary(snapshots)}

    @app.delete("/api/debug/test-snapshots/{snapshot_id}")
    async def delete_test_snapshot(snapshot_id: str):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        data = _read_test_snapshot(path)
        path.unlink()
        return {"ok": True, "snapshot": _snapshot_meta(data)}

    @app.get("/api/debug/test-snapshots/{snapshot_id}/diff")
    async def diff_test_snapshot(snapshot_id: str):
        path = _snapshot_path(snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        return _debug_snapshot_diff(_read_test_snapshot(path))

    @app.post("/api/debug/test-snapshots/load")
    async def load_test_snapshot(req: TestSnapshotLoadRequest):
        path = _snapshot_path(req.snapshot_id)
        if not path.exists():
            raise HTTPException(404, "test snapshot not found")
        data = _read_test_snapshot(path)
        try:
            state["world"].import_save(data.get("save", {}))
        except ValueError as e:
            raise HTTPException(400, str(e))
        data["last_loaded_at"] = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "snapshot": _snapshot_meta(data), "state": state["world"].snapshot()}

    @app.post("/api/reset")
    async def reset(template_id: str | None = None):
        if template_id:
            template = get_birth_template(template_id)
            if "error" in template:
                raise HTTPException(404, template["error"])
        # truncate the audit log so we start clean
        if state["audit_path"].exists():
            state["audit_path"].unlink()
        _build()
        if template_id:
            apply_birth_template(state["world"], template_id)
        return {"ok": True, "state": state["world"].snapshot()}

    return app


def main():
    """Entry point for `mingrpg-web`."""
    import uvicorn
    host = os.environ.get("MINGRPG_HOST", "127.0.0.1")
    port = int(os.environ.get("MINGRPG_PORT", "8765"))
    app = create_app()
    print(f"\n  人生纪实 web 服务运行于 http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
