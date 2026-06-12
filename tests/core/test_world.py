"""Tests for the World state layer (SQLite-backed pure data store)."""
import pytest
from mingrpg.core.world import World


@pytest.fixture
def world():
    """In-memory world for each test."""
    return World(":memory:")


# ----- Entity round-trip -----

def test_save_and_get_entity(world):
    entity = {
        "id": "player",
        "name": "无名书生",
        "type": "player",
        "location": "court_hall",
        "pos": [3, 5],
        "attributes": {"hp": 100, "max_hp": 100, "rank": "平民"},
        "status_effects": [],
        "inventory": [],
        "tags": ["protagonist"],
    }
    world.save_entity(entity)
    got = world.get_entity("player")
    assert got == entity


def test_get_unknown_entity_returns_none(world):
    assert world.get_entity("ghost") is None


def test_update_entity_overwrites(world):
    world.save_entity({"id": "wang", "name": "old", "type": "npc",
                        "location": "x", "pos": [0, 0],
                        "attributes": {"hp": 10}, "status_effects": [],
                        "inventory": [], "tags": []})
    world.save_entity({"id": "wang", "name": "new", "type": "npc",
                        "location": "x", "pos": [0, 0],
                        "attributes": {"hp": 20}, "status_effects": [],
                        "inventory": [], "tags": []})
    assert world.get_entity("wang")["name"] == "new"
    assert world.get_entity("wang")["attributes"]["hp"] == 20


# ----- Location -----

def test_save_and_get_location(world):
    loc = {
        "id": "court_hall",
        "name": "扬州府衙大堂",
        "type": "indoor_official",
        "size": [10, 10],
        "exits": {"south": "court_yard"},
        "tags": ["public", "official"],
    }
    world.save_location(loc)
    assert world.get_location("court_hall") == loc


def test_list_entities_at_location(world):
    world.save_entity({"id": "a", "name": "甲", "type": "npc",
                        "location": "hall", "pos": [0, 0],
                        "attributes": {}, "status_effects": [],
                        "inventory": [], "tags": []})
    world.save_entity({"id": "b", "name": "乙", "type": "npc",
                        "location": "hall", "pos": [1, 1],
                        "attributes": {}, "status_effects": [],
                        "inventory": [], "tags": []})
    world.save_entity({"id": "c", "name": "丙", "type": "npc",
                        "location": "yard", "pos": [0, 0],
                        "attributes": {}, "status_effects": [],
                        "inventory": [], "tags": []})
    ids = sorted(e["id"] for e in world.list_entities_at("hall"))
    assert ids == ["a", "b"]


# ----- Events (append-only) -----

def test_append_and_list_events(world):
    world.append_event({"actor": "player", "type": "move",
                         "summary": "玩家进入大堂"})
    world.append_event({"actor": "player", "type": "talk",
                         "summary": "玩家向知府行礼"})
    events = world.list_events()
    assert len(events) == 2
    assert events[0]["summary"] == "玩家进入大堂"
    assert events[1]["summary"] == "玩家向知府行礼"
    # auto-assigned ids monotonic
    assert events[0]["id"] < events[1]["id"]


def test_list_events_with_limit(world):
    for i in range(5):
        world.append_event({"actor": "player", "type": "test",
                             "summary": f"event {i}"})
    last_two = world.list_events(limit=2)
    assert len(last_two) == 2
    assert last_two[-1]["summary"] == "event 4"


# ----- Flags (key-value) -----

def test_set_and_get_flag(world):
    world.set_flag("公堂袭官", True)
    assert world.get_flag("公堂袭官") is True


def test_unset_flag_returns_none(world):
    assert world.get_flag("nothing") is None


def test_flag_overwrite(world):
    world.set_flag("count", 1)
    world.set_flag("count", 5)
    assert world.get_flag("count") == 5


# ----- World time -----

def test_default_world_time(world):
    t = world.get_world_time()
    assert "year" in t and "season" in t and "time_of_day" in t


def test_set_world_time(world):
    world.set_world_time({"year": "万历十年", "season": "秋",
                           "time_of_day": "子时"})
    t = world.get_world_time()
    assert t["year"] == "万历十年"
    assert t["time_of_day"] == "子时"


# ----- Snapshot -----

def test_default_world_time_has_day_index(world):
    t = world.get_world_time()
    assert "day_index" in t
    assert t["day_index"] == 0


def test_snapshot_contains_all_layers(world):
    world.save_entity({"id": "p", "name": "p", "type": "player",
                        "location": "h", "pos": [0, 0],
                        "attributes": {}, "status_effects": [],
                        "inventory": [], "tags": []})
    world.save_location({"id": "h", "name": "h", "type": "x",
                          "size": [1, 1], "exits": {}, "tags": []})
    world.set_flag("x", True)
    snap = world.snapshot()
    assert "entities" in snap
    assert "locations" in snap
    assert "flags" in snap
    assert "time" in snap
    assert len(snap["entities"]) == 1
    assert len(snap["locations"]) == 1
    assert snap["flags"]["x"] is True


# ----- Shareable saves -----

def test_export_save_contains_full_world(world):
    world.save_entity({"id": "p", "name": "p", "type": "player",
                        "location": "h", "pos": [0, 0],
                        "attributes": {"hp": 88}, "status_effects": [],
                        "inventory": [], "tags": []})
    world.save_location({"id": "h", "name": "h", "type": "x",
                          "size": [1, 1], "exits": {}, "tags": []})
    world.append_event({"actor": "p", "type": "note", "summary": "saved"})
    world.set_flag("story_progress", {"main_thread": {"clues": ["x"]}})

    save = world.export_save()

    assert save["format"] == "mingrpg.save"
    assert save["version"] == 1
    assert save["world"]["entities"][0]["attributes"]["hp"] == 88
    assert save["world"]["events"][0]["summary"] == "saved"
    assert save["world"]["flags"]["story_progress"]["main_thread"]["clues"] == ["x"]
    assert save["world"]["time"]["day_index"] == 0


def test_import_save_restores_world(world):
    world.save_entity({"id": "old", "name": "old", "type": "npc",
                        "location": "old_loc", "pos": [0, 0],
                        "attributes": {}, "status_effects": [],
                        "inventory": [], "tags": []})
    save = {
        "format": "mingrpg.save",
        "version": 1,
        "world": {
            "entities": [{"id": "p", "name": "p", "type": "player",
                          "location": "h", "pos": [2, 3],
                          "attributes": {"hp": 77}, "status_effects": [],
                          "inventory": [], "tags": []}],
            "locations": [{"id": "h", "name": "h", "type": "x",
                           "size": [1, 1], "exits": {}, "tags": []}],
            "events": [{"actor": "p", "type": "note", "summary": "imported"}],
            "flags": {"x": True},
            "time": {"year": "万历十年", "time_of_day": "午时", "day_index": 2},
        },
    }

    world.import_save(save)

    assert world.get_entity("old") is None
    assert world.get_entity("p")["attributes"]["hp"] == 77
    assert world.get_location("h")["name"] == "h"
    assert world.list_events()[0]["summary"] == "imported"
    assert world.get_flag("x") is True
    assert world.get_world_time()["day_index"] == 2


def test_import_save_rejects_unknown_format(world):
    with pytest.raises(ValueError, match="unsupported save format"):
        world.import_save({"format": "other", "version": 1, "world": {}})
