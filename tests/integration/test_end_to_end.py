"""End-to-end integration test using the real LLM endpoint.

Marked as 'live' so it can be skipped in non-network environments.
"""
import json
import os
import pytest

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.world import World
from mingrpg.llm.agent import GMAgent
from mingrpg.scenarios.yangzhou_court import seed_yangzhou_court


pytestmark = pytest.mark.skipif(
    os.environ.get("MINGRPG_RUN_LIVE") != "1",
    reason="live LLM integration test; set MINGRPG_RUN_LIVE=1 to run",
)


API_KEY = "tp-srtg3w0atiqiyhe84myptmcnc4xnyg6j0ej5vn8d0eoceswx"
BASE_URL = "https://token-plan-sgp.xiaomimimo.com/anthropic"
MODEL = "mimo-v2.5-pro"


@pytest.fixture
def setup(tmp_path):
    world = World(":memory:")
    seed_yangzhou_court(world)
    audit = AuditLogger(tmp_path / "audit.jsonl")
    agent = GMAgent(world=world, audit=audit, model=MODEL,
                     api_key=API_KEY, base_url=BASE_URL)
    return world, audit, agent, tmp_path


def test_polite_action_does_not_cite_violence_law(setup):
    """温和动作不应触发暴力法条。"""
    _, _, agent, tmp_path = setup
    agent.process_input("我安静地站着,等候知府发问。")
    log = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip()
    rec = json.loads(log)
    cited = " ".join(rec["cited_laws"])
    assert "斗殴" not in cited or rec["cited_laws"] == []


def test_violent_action_against_official_cites_law(setup):
    """殴打知府必须引用相关法律。"""
    _, _, agent, tmp_path = setup
    agent.process_input("我冲上去给王知府一拳!")
    log = (tmp_path / "audit.jsonl").read_text(encoding="utf-8").strip()
    rec = json.loads(log)
    # 应当至少引用一条与殴官或斗殴相关的法条
    assert any("斗殴" in lid or "殴" in lid for lid in rec["cited_laws"]), \
        f"expected violence law to be cited, got: {rec['cited_laws']}"


def test_violent_action_leaves_consequences(setup):
    """殴打知府后玩家应当被加上状态(被擒/通缉)或被移到监狱。"""
    world, _, agent, _ = setup
    agent.process_input("我抽出袖中匕首,猛地刺向知府!")
    player = world.get_entity("player")
    statuses = [s["name"] for s in player["status_effects"]]
    in_jail = player["location"] == "jail"
    has_bad_status = any(
        s in "".join(statuses)
        for s in ["擒", "押", "通缉", "拘", "捕", "缚", "镣", "锁"]
    )
    assert in_jail or has_bad_status, \
        f"expected jail or restraint status, got: location={player['location']}, statuses={statuses}"


def test_writes_are_recorded_in_audit(setup):
    """任何修改都应当在 writes 字段被记录。"""
    _, _, agent, tmp_path = setup
    agent.process_input("我向知府行礼,呈上状纸。")
    rec = json.loads((tmp_path / "audit.jsonl").read_text().strip())
    # 至少应当 log_event 一次记录此事件
    write_tools = [w["tool"] for w in rec["writes"]]
    assert "log_event" in write_tools or "add_memory" in write_tools
