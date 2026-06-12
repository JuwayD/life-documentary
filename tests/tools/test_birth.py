"""Tests for birth setting tools."""
from pathlib import Path

from mingrpg.core.world import World
from mingrpg.scenarios.yangzhou_court import seed_yangzhou_court
from mingrpg.tools import birth as B


def test_list_birth_templates_loads_real_defaults(monkeypatch):
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "birth_templates")
    monkeypatch.setattr(B, "_BIRTH_TEMPLATE_DIR", real_dir)
    B._reset_birth_templates_cache()

    result = B.list_birth_templates()

    ids = {t["id"] for t in result["templates"]}
    assert {"scholar", "merchant_son", "military_heir", "beggar"} <= ids
    scholar = next(t for t in result["templates"] if t["id"] == "scholar")
    assert scholar["name"] == "落第书生"
    assert scholar["money_wen"] == 50
    assert scholar["start"]["location"] == "court_hall"


def test_get_birth_template_returns_full_template(monkeypatch):
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "birth_templates")
    monkeypatch.setattr(B, "_BIRTH_TEMPLATE_DIR", real_dir)
    B._reset_birth_templates_cache()

    template = B.get_birth_template("merchant_son")

    assert template["name"] == "商人之子"
    assert template["attributes"]["skills"]["commerce"]["name"] == "商贸"
    assert any(item["id"] == "account_slip" for item in template["inventory"])


def test_get_birth_template_unknown_returns_error(tmp_path, monkeypatch):
    monkeypatch.setattr(B, "_BIRTH_TEMPLATE_DIR", str(tmp_path))
    B._reset_birth_templates_cache()

    result = B.get_birth_template("ghost")

    assert "error" in result
    assert "ghost" in result["error"]


def test_apply_birth_template_updates_player_and_records_flag(monkeypatch):
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "birth_templates")
    monkeypatch.setattr(B, "_BIRTH_TEMPLATE_DIR", real_dir)
    B._reset_birth_templates_cache()
    world = World(":memory:")
    seed_yangzhou_court(world)

    result = B.apply_birth_template(world, "military_heir")

    player = world.get_entity("player")
    assert result["template_id"] == "military_heir"
    assert player["name"] == "武将后代"
    assert player["location"] == "court_yard"
    assert world.get_location(player["location"]) is not None
    assert player["pos"] == [6, 6]
    assert player["attributes"]["hp"] == 34
    assert player["attributes"]["skills"]["martial_arts"]["name"] == "武艺"
    assert player["inventory"] == [{"id": "wooden_staff", "name": "木棍", "qty": 1, "damage": 6}]
    assert player["status_effects"] == []
    assert world.get_flag("birth_setting")["template_id"] == "military_heir"
    assert world.list_events(limit=1)[0]["type"] == "birth_template_applied"


def test_apply_birth_template_unknown_returns_error(monkeypatch):
    real_dir = str(Path(__file__).parent.parent.parent / "data" / "birth_templates")
    monkeypatch.setattr(B, "_BIRTH_TEMPLATE_DIR", real_dir)
    B._reset_birth_templates_cache()
    world = World(":memory:")
    seed_yangzhou_court(world)

    result = B.apply_birth_template(world, "ghost")

    assert "error" in result
    assert world.get_entity("player")["name"] == "无名书生"
