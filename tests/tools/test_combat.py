"""Tests for combat tools — skill_check, apply_damage, tick_statuses, and add_status extension."""
import pytest
from mingrpg.core.world import World
from mingrpg.tools import util as U
from mingrpg.tools import write as W


# ============================================================================
# skill_check (util.py — pure function)
# ============================================================================

class TestSkillCheck:
    def test_success_when_total_meets_dc(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 12)
        r = U.skill_check(attribute_value=3, dc=15)
        assert r["roll"] == 12
        assert r["modifier"] == 3
        assert r["total"] == 15
        assert r["dc"] == 15
        assert r["success"] is True
        assert r["margin"] == 0
        assert r["critical"] is False

    def test_failure_when_total_below_dc(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 10)
        r = U.skill_check(attribute_value=3, dc=15)
        assert r["success"] is False
        assert r["margin"] == -2

    def test_margin_is_positive_on_great_success(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 18)
        r = U.skill_check(attribute_value=3, dc=15)
        assert r["success"] is True
        assert r["margin"] == 6

    def test_critical_success_on_natural_20(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 20)
        r = U.skill_check(attribute_value=0, dc=25)
        assert r["roll"] == 20
        assert r["success"] is True
        assert r["critical"] is True
        assert r["total"] == 20

    def test_critical_failure_on_natural_1(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 1)
        r = U.skill_check(attribute_value=5, dc=5)
        assert r["roll"] == 1
        assert r["success"] is False
        assert r["critical"] is True

    def test_advantage_takes_higher_of_two(self, monkeypatch):
        calls = iter([8, 16])
        monkeypatch.setattr("random.randint", lambda a, b: next(calls))
        r = U.skill_check(attribute_value=3, dc=15, advantage=True)
        assert r["roll"] == 16
        assert r["total"] == 19
        assert r["success"] is True

    def test_explicit_modifier_adds_to_total(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 10)
        r = U.skill_check(attribute_value=2, dc=14, modifier=2)
        assert r["modifier"] == 4
        assert r["total"] == 14

    def test_dc_string_converts_to_int(self, monkeypatch):
        monkeypatch.setattr("random.randint", lambda a, b: 15)
        r = U.skill_check(attribute_value=2, dc="15")
        assert r["dc"] == 15
        assert r["success"] is True


# ============================================================================
# apply_damage (write.py)
# ============================================================================

@pytest.fixture
def cw():
    """Combat test world with player and guard."""
    world = World(":memory:")
    world.save_entity({
        "id": "player", "name": "无名书生", "type": "player",
        "location": "hall", "pos": [3, 5],
        "attributes": {"hp": 100, "max_hp": 100, "str": 10, "dex": 12},
        "status_effects": [], "inventory": [], "tags": [],
    })
    world.save_entity({
        "id": "guard", "name": "衙役甲", "type": "npc",
        "location": "hall", "pos": [3, 7],
        "attributes": {"hp": 60, "max_hp": 60, "attack": 4, "defense": 12,
                        "weapon_damage": "1d6", "weapon_name": "腰刀"},
        "status_effects": [], "inventory": [], "tags": ["guard"],
    })
    return world


class TestApplyDamage:
    def test_reduces_hp_and_returns_diff(self, cw):
        r = W.apply_damage(cw, "guard", 5, damage_type="physical", source="player")
        assert r["entity"] == "guard"
        assert r["old_hp"] == 60
        assert r["new_hp"] == 55
        assert r["amount"] == 5
        assert r["overkill"] == 0
        assert r["incapacitated"] is False
        assert cw.get_entity("guard")["attributes"]["hp"] == 55

    def test_clamps_to_zero_and_flags_incapacitated(self, cw):
        r = W.apply_damage(cw, "guard", 70)
        assert r["new_hp"] == 0
        assert r["amount"] == 70
        assert r["overkill"] == 10
        assert r["incapacitated"] is True
        assert cw.get_entity("guard")["attributes"]["hp"] == 0

    def test_exact_lethal_damage(self, cw):
        r = W.apply_damage(cw, "guard", 60)
        assert r["new_hp"] == 0
        assert r["overkill"] == 0
        assert r["incapacitated"] is True

    def test_unknown_entity_returns_error(self, cw):
        r = W.apply_damage(cw, "ghost", 10)
        assert "error" in r

    def test_zero_damage_is_allowed(self, cw):
        r = W.apply_damage(cw, "guard", 0)
        assert r["new_hp"] == 60
        assert r["incapacitated"] is False

    def test_default_params(self, cw):
        r = W.apply_damage(cw, "guard", 5)
        assert r["damage_type"] == "physical"
        assert r["source"] == ""

    def test_already_at_zero(self, cw):
        e = cw.get_entity("guard")
        e["attributes"]["hp"] = 0
        cw.save_entity(e)
        r = W.apply_damage(cw, "guard", 5)
        assert r["new_hp"] == 0
        assert r["overkill"] == 5
        assert r["incapacitated"] is True


# ============================================================================
# tick_statuses (write.py)
# ============================================================================

@pytest.fixture
def tw():
    """Tick test world with entities that have various status effects."""
    world = World(":memory:")
    world.save_entity({
        "id": "player", "name": "无名书生", "type": "player",
        "location": "hall", "pos": [3, 5],
        "attributes": {"hp": 100, "max_hp": 100},
        "status_effects": [
            {"name": "流血", "duration": 3, "reason": "刀伤",
             "damage_per_tick": 2, "effect_type": "bleeding"},
        ],
        "inventory": [], "tags": [],
    })
    world.save_entity({
        "id": "guard", "name": "衙役甲", "type": "npc",
        "location": "hall", "pos": [3, 7],
        "attributes": {"hp": 60, "max_hp": 60},
        "status_effects": [
            {"name": "眩晕", "duration": 1, "reason": "当头一击",
             "damage_per_tick": 0, "effect_type": "stun"},
        ],
        "inventory": [], "tags": ["guard"],
    })
    world.save_entity({
        "id": "npc_clean", "name": "路人", "type": "npc",
        "location": "hall", "pos": [5, 5],
        "attributes": {"hp": 50, "max_hp": 50},
        "status_effects": [], "inventory": [], "tags": [],
    })
    return world


class TestTickStatuses:
    def test_decrements_duration(self, tw):
        r = W.tick_statuses(tw, "player")
        assert len(r["ticked"]) == 1
        t = r["ticked"][0]
        assert t["entity"] == "player"
        assert t["status"] == "流血"
        assert t["new_duration"] == 2
        assert t["expired"] is False
        se = tw.get_entity("player")["status_effects"]
        assert se[0]["duration"] == 2

    def test_removes_expired_status(self, tw):
        r = W.tick_statuses(tw, "guard")
        t = r["ticked"][0]
        assert t["expired"] is True
        assert tw.get_entity("guard")["status_effects"] == []

    def test_applies_damage_per_tick(self, tw):
        r = W.tick_statuses(tw, "player")
        t = r["ticked"][0]
        assert t["damage_dealt"] == 2
        assert tw.get_entity("player")["attributes"]["hp"] == 98

    def test_skips_permanent_effects(self, tw):
        # Add a permanent effect (duration=-1)
        e = tw.get_entity("player")
        e["status_effects"].append(
            {"name": "通缉", "duration": -1, "reason": "官府",
             "damage_per_tick": 0, "effect_type": "wanted"},
        )
        tw.save_entity(e)
        r = W.tick_statuses(tw, "player")
        durations = {t["status"]: t["new_duration"] for t in r["ticked"]}
        assert durations["通缉"] == -1
        assert "通缉" in [s["name"] for s in tw.get_entity("player")["status_effects"]]

    def test_all_entities_when_no_id(self, tw):
        r = W.tick_statuses(tw)
        ticked_ids = {t["entity"] for t in r["ticked"]}
        assert "player" in ticked_ids
        assert "guard" in ticked_ids
        # npc_clean has no status effects, should not appear
        assert "npc_clean" not in ticked_ids

    def test_unknown_entity_returns_error(self, tw):
        r = W.tick_statuses(tw, "ghost")
        assert "error" in r

    def test_no_status_effects_returns_empty(self, tw):
        r = W.tick_statuses(tw, "npc_clean")
        assert r["ticked"] == []

    def test_damage_per_tick_can_kill(self, tw):
        # Set up a bleeding entity with very low HP
        e = tw.get_entity("guard")
        e["attributes"]["hp"] = 2
        e["status_effects"] = [
            {"name": "流血", "duration": 3, "reason": "重伤",
             "damage_per_tick": 5, "effect_type": "bleeding"},
        ]
        tw.save_entity(e)
        r = W.tick_statuses(tw, "guard")
        t = r["ticked"][0]
        assert t["damage_dealt"] == 5
        assert tw.get_entity("guard")["attributes"]["hp"] == 0


# ============================================================================
# add_status — extended with damage_per_tick / effect_type
# ============================================================================

class TestAddStatusExtended:
    def test_preserves_damage_per_tick_field(self, cw):
        r = W.add_status(cw, "player", "中毒", duration=3,
                         reason="被蛇咬", damage_per_tick=2, effect_type="poison")
        assert r["status"] == "中毒"
        se = cw.get_entity("player")["status_effects"]
        assert se[0]["damage_per_tick"] == 2
        assert se[0]["effect_type"] == "poison"
        assert se[0]["duration"] == 3

    def test_damage_per_tick_defaults_to_zero(self, cw):
        W.add_status(cw, "player", "眩晕", duration=1, reason="重击")
        se = cw.get_entity("player")["status_effects"]
        assert se[0]["damage_per_tick"] == 0
        assert "effect_type" not in se[0]
