"""Utility tools — pure mathematical helpers exposed to GM Agent.

No world state, no decisions. Just calculations.
"""
import math
import random
import re


# ---------------------------------------------------------------------------
# Dice
# ---------------------------------------------------------------------------
_DICE_RE = re.compile(r"^\s*(\d+)d(\d+)\s*([+\-]\s*\d+)?\s*$",
                       re.IGNORECASE)


def roll_dice(notation: str) -> dict:
    """Roll dice in standard D&D notation: NdM, NdM+K, NdM-K.

    Returns {rolls, modifier, total, notation}.
    """
    m = _DICE_RE.match(notation)
    if not m:
        return {"error": f"invalid dice notation: '{notation}'",
                "suggestion": "use e.g. '1d20', '3d6+2', '1d100-5'"}
    n = int(m.group(1))
    sides = int(m.group(2))
    mod_str = (m.group(3) or "").replace(" ", "")
    modifier = int(mod_str) if mod_str else 0

    if n <= 0 or sides <= 0:
        return {"error": "dice count and sides must be positive"}
    if n > 100 or sides > 1000:
        return {"error": "dice limits exceeded (max 100 dice, 1000 sides)"}

    rolls = [random.randint(1, sides) for _ in range(n)]
    total = sum(rolls) + modifier
    return {
        "notation": notation,
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
    }


# ---------------------------------------------------------------------------
# Skill Check
# ---------------------------------------------------------------------------
def skill_check(attribute_value: int, dc: int, modifier: int = 0,
                advantage: bool = False) -> dict:
    """Perform a D&D-style skill check: roll 1d20 + attribute_value + modifier vs DC.

    Returns {roll, modifier, total, dc, success, margin, critical}.
    Natural 20 = critical success, natural 1 = critical failure.
    advantage=True rolls twice and takes the higher result.
    """
    dc = int(dc)
    total_modifier = attribute_value + modifier
    if advantage:
        r1 = random.randint(1, 20)
        r2 = random.randint(1, 20)
        roll = max(r1, r2)
    else:
        roll = random.randint(1, 20)

    total = roll + total_modifier
    critical = roll == 20 or roll == 1
    success = (roll == 20) or (total >= dc and roll != 1)
    margin = total - dc

    return {
        "roll": roll,
        "modifier": total_modifier,
        "total": total,
        "dc": dc,
        "success": success,
        "margin": margin,
        "critical": critical,
    }


# ---------------------------------------------------------------------------
# Distance
# ---------------------------------------------------------------------------
def calculate_distance(from_pos: list, to_pos: list) -> dict:
    """Return Euclidean / Chebyshev / Manhattan distances between two points."""
    dx = to_pos[0] - from_pos[0]
    dy = to_pos[1] - from_pos[1]
    return {
        "distance": round(math.sqrt(dx * dx + dy * dy), 2),
        "chebyshev": max(abs(dx), abs(dy)),
        "manhattan": abs(dx) + abs(dy),
        "from": list(from_pos),
        "to": list(to_pos),
    }
