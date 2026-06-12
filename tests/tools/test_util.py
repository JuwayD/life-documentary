"""Tests for utility tools — pure functions, no world state."""
import pytest
from mingrpg.tools import util as U


# ----- roll_dice -----

def test_roll_dice_simple(monkeypatch):
    """1d20 should return one roll in [1, 20]."""
    monkeypatch.setattr("random.randint", lambda a, b: 15)
    r = U.roll_dice("1d20")
    assert r["rolls"] == [15]
    assert r["modifier"] == 0
    assert r["total"] == 15
    assert r["notation"] == "1d20"


def test_roll_dice_with_modifier(monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 10)
    r = U.roll_dice("1d20+5")
    assert r["rolls"] == [10]
    assert r["modifier"] == 5
    assert r["total"] == 15


def test_roll_dice_negative_modifier(monkeypatch):
    monkeypatch.setattr("random.randint", lambda a, b: 18)
    r = U.roll_dice("1d20-3")
    assert r["modifier"] == -3
    assert r["total"] == 15


def test_roll_dice_multiple(monkeypatch):
    """3d6 should roll three dice and sum them."""
    calls = iter([3, 4, 6])
    monkeypatch.setattr("random.randint", lambda a, b: next(calls))
    r = U.roll_dice("3d6")
    assert r["rolls"] == [3, 4, 6]
    assert r["total"] == 13


def test_roll_dice_invalid_notation():
    r = U.roll_dice("bogus")
    assert "error" in r


def test_roll_dice_real_randomness_range():
    """Smoke test that real RNG produces sane values."""
    for _ in range(20):
        r = U.roll_dice("1d20")
        assert 1 <= r["rolls"][0] <= 20


# ----- calculate_distance -----

def test_calc_distance_same_point():
    assert U.calculate_distance([3, 5], [3, 5])["distance"] == 0.0


def test_calc_distance_orthogonal():
    r = U.calculate_distance([0, 0], [3, 4])
    assert r["distance"] == 5.0
    assert r["chebyshev"] == 4  # max(3, 4)
    assert r["manhattan"] == 7


def test_calc_distance_negative_coords():
    r = U.calculate_distance([-1, -1], [2, 3])
    assert r["distance"] == 5.0
