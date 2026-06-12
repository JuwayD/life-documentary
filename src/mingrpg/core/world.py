"""World state — pure data store backed by SQLite.

This is the single source of truth for all game state. No business logic,
no validation beyond what SQLite provides.
"""
import json
import sqlite3
from datetime import datetime


SAVE_FORMAT = "mingrpg.save"
SAVE_VERSION = 1


class World:
    """In-memory world backed by SQLite."""

    def __init__(self, db_path: str = ":memory:"):
        # check_same_thread=False allows the connection to be used across
        # threads (e.g. FastAPI's threadpool for sync endpoints). The game
        # is single-player and turns are serialised, so true concurrent
        # writes don't happen.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self._ensure_default_time()

    # ----------------------------------------------------------------
    # Schema
    # ----------------------------------------------------------------
    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                json_data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS locations (
                id TEXT PRIMARY KEY,
                json_data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                json_data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS flags (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS world_time (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                json_data TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def _ensure_default_time(self):
        row = self._conn.execute(
            "SELECT 1 FROM world_time WHERE id = 1").fetchone()
        if not row:
            self.set_world_time({
                "year": "万历十年",
                "season": "秋",
                "time_of_day": "巳时",
                "date": "辛卯",
                "day_index": 0,
            })

    # ----------------------------------------------------------------
    # Entity operations
    # ----------------------------------------------------------------
    def save_entity(self, entity: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO entities (id, json_data) VALUES (?, ?)",
            (entity["id"], json.dumps(entity, ensure_ascii=False)))
        self._conn.commit()

    def get_entity(self, entity_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT json_data FROM entities WHERE id = ?",
            (entity_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def delete_entity(self, entity_id: str) -> None:
        self._conn.execute(
            "DELETE FROM entities WHERE id = ?", (entity_id,))
        self._conn.commit()

    # ----------------------------------------------------------------
    # Location operations
    # ----------------------------------------------------------------
    def save_location(self, location: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO locations (id, json_data) VALUES (?, ?)",
            (location["id"], json.dumps(location, ensure_ascii=False)))
        self._conn.commit()

    def get_location(self, location_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT json_data FROM locations WHERE id = ?",
            (location_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_entities_at(self, location_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT json_data FROM entities WHERE "
            "json_extract(json_data, '$.location') = ?",
            (location_id,)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_entities(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT json_data FROM entities").fetchall()
        return [json.loads(r[0]) for r in rows]

    def list_locations(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT json_data FROM locations").fetchall()
        return [json.loads(r[0]) for r in rows]

    # ----------------------------------------------------------------
    # Event operations (append-only)
    # ----------------------------------------------------------------
    def append_event(self, event: dict) -> int:
        c = self._conn.execute(
            "INSERT INTO events (json_data) VALUES (?)",
            (json.dumps(event, ensure_ascii=False),))
        self._conn.commit()
        return c.lastrowid

    def list_events(self, limit: int = 50) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, json_data FROM events ORDER BY id DESC LIMIT ?",
            (limit,)).fetchall()
        result = []
        for r in reversed(rows):
            ev = json.loads(r[1])
            ev["id"] = r[0]
            result.append(ev)
        return result

    # ----------------------------------------------------------------
    # Flag operations (key-value)
    # ----------------------------------------------------------------
    def set_flag(self, key: str, value) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO flags (key, value) VALUES (?, ?)",
            (key, json.dumps(value)))
        self._conn.commit()

    def get_flag(self, key: str):
        row = self._conn.execute(
            "SELECT value FROM flags WHERE key = ?",
            (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def all_flags(self) -> dict:
        rows = self._conn.execute("SELECT key, value FROM flags").fetchall()
        return {r[0]: json.loads(r[1]) for r in rows}

    # ----------------------------------------------------------------
    # World time
    # ----------------------------------------------------------------
    def get_world_time(self) -> dict:
        row = self._conn.execute(
            "SELECT json_data FROM world_time WHERE id = 1").fetchone()
        return json.loads(row[0]) if row else {}

    def set_world_time(self, time_data: dict) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO world_time (id, json_data) VALUES (1, ?)",
            (json.dumps(time_data, ensure_ascii=False),))
        self._conn.commit()

    # ----------------------------------------------------------------
    # Snapshot (for LLM context building)
    # ----------------------------------------------------------------
    def snapshot(self) -> dict:
        flags = self.all_flags()
        return {
            "entities": [
                json.loads(r[0]) for r in
                self._conn.execute("SELECT json_data FROM entities").fetchall()
            ],
            "locations": [
                json.loads(r[0]) for r in
                self._conn.execute(
                    "SELECT json_data FROM locations").fetchall()
            ],
            "events": self.list_events(limit=10),
            "flags": flags,
            "time": self.get_world_time(),
            "evolutions": flags.get("evolution_registry", []),
        }

    def export_save(self) -> dict:
        return {
            "format": SAVE_FORMAT,
            "version": SAVE_VERSION,
            "world": {
                "entities": [
                    json.loads(r[0]) for r in
                    self._conn.execute(
                        "SELECT json_data FROM entities ORDER BY id").fetchall()
                ],
                "locations": [
                    json.loads(r[0]) for r in
                    self._conn.execute(
                        "SELECT json_data FROM locations ORDER BY id").fetchall()
                ],
                "events": [
                    json.loads(r[0]) for r in
                    self._conn.execute(
                        "SELECT json_data FROM events ORDER BY id").fetchall()
                ],
                "flags": self.all_flags(),
                "time": self.get_world_time(),
            },
        }

    def import_save(self, save_data: dict) -> None:
        if save_data.get("format") != SAVE_FORMAT:
            raise ValueError("unsupported save format")
        if save_data.get("version") != SAVE_VERSION:
            raise ValueError("unsupported save version")

        world = save_data.get("world")
        if not isinstance(world, dict):
            raise ValueError("missing world data")

        with self._conn:
            self._conn.execute("DELETE FROM entities")
            self._conn.execute("DELETE FROM locations")
            self._conn.execute("DELETE FROM events")
            self._conn.execute("DELETE FROM flags")
            self._conn.execute("DELETE FROM world_time")

            for entity in world.get("entities", []):
                self._conn.execute(
                    "INSERT INTO entities (id, json_data) VALUES (?, ?)",
                    (entity["id"], json.dumps(entity, ensure_ascii=False)))
            for location in world.get("locations", []):
                self._conn.execute(
                    "INSERT INTO locations (id, json_data) VALUES (?, ?)",
                    (location["id"], json.dumps(location, ensure_ascii=False)))
            for event in world.get("events", []):
                self._conn.execute(
                    "INSERT INTO events (json_data) VALUES (?)",
                    (json.dumps(event, ensure_ascii=False),))
            for key, value in world.get("flags", {}).items():
                self._conn.execute(
                    "INSERT INTO flags (key, value) VALUES (?, ?)",
                    (key, json.dumps(value, ensure_ascii=False)))
            self._conn.execute(
                "INSERT OR REPLACE INTO world_time (id, json_data) VALUES (1, ?)",
                (json.dumps(world.get("time", {}), ensure_ascii=False),))

    # ------------------------------------------------------------------
    # Event-sourced replay (format v2)
    # ------------------------------------------------------------------
    def export_replay_log(self, audit_path: str) -> dict:
        """Build a replay log from this world + audit trail."""
        from mingrpg.core.replay import export_replay_log
        return export_replay_log(self, audit_path)

    def import_replay_log(self, replay_data: dict) -> None:
        """Replay an event-sourced log into this world (destructive)."""
        from mingrpg.core.replay import replay_from_log
        replay_from_log(replay_data, target_world=self)

    def close(self):
        self._conn.close()