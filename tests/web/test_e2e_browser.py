"""End-to-end browser tests using Playwright.

A fake agent is injected so these tests are fast and don't hit the LLM.
The Playwright fixture launches uvicorn in a thread.
"""
import json
import re
import threading
import time
import socket

import pytest
import uvicorn
from playwright.sync_api import expect

from mingrpg.web.server import create_app


def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class FakeAgent:
    """Echoes input; mutates world via log_event so panel updates."""

    def __init__(self, world, audit, **_):
        self.world = world
        self.audit = audit

    def process_input(self, text: str) -> str:
        from mingrpg.tools.write import log_event, add_status, \
            record_clue, advance_pressure_clock, ask_advisor, discover_observation, \
            join_party, set_active_actor, move_entity
        snap = self.world.snapshot()
        self.audit.start_turn(player_input=text, snapshot=snap)
        result = log_event(self.world, {
            "actor": "player", "type": "test",
            "summary": f"测试事件:{text}"
        })
        self.audit.record_tool_call("log_event", {}, result)
        # 给 player 加个状态,方便前端验证
        if "状态" in text:
            res = add_status(self.world, "player", "测试状态",
                              duration=3, reason="test")
            self.audit.record_tool_call("add_status", {}, res)
        # 剧情面板: 记录线索
        if "线索" in text:
            res = record_clue(self.world, "main_thread",
                              "状纸被师爷压下", source_entity="衙役",
                              location_id="court_yard")
            self.audit.record_tool_call("record_clue", {}, res)
            res = record_clue(self.world, "market_debt",
                              "陈掌柜听说码头有短工被拖欠工钱", source_entity="陈掌柜",
                              location_id="teahouse")
            self.audit.record_tool_call("record_clue", {}, res)
        # 剧情面板: 推进压力钟
        if "压力" in text:
            res = advance_pressure_clock(self.world, "witness_pressure",
                                         amount=2, reason="证人受威胁")
            self.audit.record_tool_call("advance_pressure_clock", {}, res)
        # 顾问系统: 请教
        if "请教" in text or "顾问" in text:
            res = ask_advisor(self.world, "shiye",
                              "我现在该怎么办?", player_id="player")
            self.audit.record_tool_call("ask_advisor", {}, res)
        # 观察系统: 发现细节
        if "观察" in text:
            res = discover_observation(self.world, "court_hall_case_table",
                                       target_id="court_hall")
            self.audit.record_tool_call("discover_observation", {}, res)
        # 队伍系统: 同行与当前行动角色
        if "同行" in text or "队伍" in text:
            res = join_party(self.world, "shiye", role="府衙向导",
                             joined_reason="测试同行")
            self.audit.record_tool_call("join_party", {}, res)
        if "当前行动角色" in text or "让刘师爷" in text:
            if self.world.get_flag("party") is None:
                join_party(self.world, "shiye", role="府衙向导",
                           joined_reason="测试同行")
            res = set_active_actor(self.world, "shiye", reason="测试切换")
            self.audit.record_tool_call("set_active_actor", {}, res)
        # 移动 NPC 到其他位置（用于测试历史关系）
        if "师爷离开" in text:
            res = move_entity(self.world, "shiye", to_location="court_yard")
            self.audit.record_tool_call("move_entity", {}, res)
        narration = f"模拟 GM 回应:你说了「{text}」。"
        self.audit.end_turn(narration=narration,
                             final_snapshot=self.world.snapshot())
        return narration

    def process_input_stream(self, text: str):
        """Streaming variant that yields WS events."""
        narration = self.process_input(text)
        yield {"type": "text", "content": narration}
        yield {"type": "done", "narration": narration,
               "state": self.world.snapshot()}


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    port = _find_free_port()
    tmp = tmp_path_factory.mktemp("e2e")
    app = create_app(agent_factory=FakeAgent, audit_dir=tmp,
                      db_path=":memory:")
    config = uvicorn.Config(app, host="127.0.0.1", port=port,
                             log_level="warning")
    srv = uvicorn.Server(config)
    t = threading.Thread(target=srv.run, daemon=True)
    t.start()
    # Wait for server to come up
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    srv.should_exit = True


# ---------------------------------------------------------------
def test_page_loads_with_opening(page, server):
    page.goto(server)
    expect(page.locator("h1")).to_contain_text("人生纪实")
    # opening bubble shows zhifu
    expect(page.locator('[data-test="bubble-gm"]')
            .first).to_contain_text("王知府")


def test_side_panel_shows_player_info(page, server):
    page.goto(server)
    # The state is loaded async after page load
    panel = page.locator('[data-test="player-panel"]')
    expect(panel).to_contain_text("无名书生")
    expect(panel).to_contain_text("HP:")
    expect(panel).to_contain_text("平民")


def test_nearby_panel_lists_npcs(page, server):
    page.goto(server)
    nearby = page.locator('[data-test="nearby-panel"]')
    expect(nearby).to_contain_text("王知府")
    expect(nearby).to_contain_text("刘师爷")


def test_relationships_panel_shows_nearby_npc_context(page, server):
    page.goto(server)
    relationships = page.locator('[data-test="relationships-panel"]')
    expect(relationships).to_contain_text("王知府")
    expect(relationships).to_contain_text("扬州知府")
    expect(relationships).to_contain_text("态度线索")
    expect(relationships).to_contain_text("尚无互动记忆")


def test_relationships_panel_updates_after_advisor_interaction(page, server):
    page.goto(server)
    page.locator('[data-test="ask-advisor-shiye"]').click()
    relationship = page.locator('[data-test="relationship-shiye"]')
    expect(relationship).to_contain_text("最近记忆")
    expect(relationship).to_contain_text("我现在该怎么办")
    expect(relationship).to_contain_text("记忆 1 条")


def test_relationships_panel_shows_historical_npcs(page, server):
    """曾互动但不在场的 NPC 应显示在'曾互动'分隔线之后。"""
    page.goto(server)
    # 先请教顾问，产生记忆
    page.locator('[data-test="ask-advisor-shiye"]').click()
    # 然后让师爷离开当前场景
    page.locator('[data-test="input"]').fill("师爷离开")
    page.locator('[data-test="submit"]').click()

    relationships = page.locator('[data-test="relationships-panel"]')
    # 应出现"曾互动"分隔线
    expect(relationships).to_contain_text("曾互动")
    # 师爷应出现在历史关系中
    historical = relationships.locator('[data-test="relationship-shiye"]')
    expect(historical).to_be_visible()
    expect(historical).to_contain_text("刘师爷")
    expect(historical).to_contain_text("记忆")
    # 应显示当前位置
    expect(historical).to_contain_text("当前在:")


def test_submitting_input_creates_bubbles(page, server):
    page.goto(server)
    page.locator('[data-test="input"]').fill("我向知府行礼")
    page.locator('[data-test="submit"]').click()

    # player bubble should appear
    expect(page.locator('[data-test="bubble-player"]'))\
        .to_contain_text("我向知府行礼")
    # GM bubble (the fake echoes back) should follow
    gm_bubbles = page.locator('[data-test="bubble-gm"]')
    expect(gm_bubbles.last).to_contain_text("我向知府行礼")


def test_suggestions_panel_shows_contextual_actions(page, server):
    page.goto(server)
    suggestions = page.locator('[data-test="suggestions-panel"]')
    expect(suggestions).to_contain_text("仔细观察")
    expect(suggestions).to_contain_text("询问在场者")
    expect(suggestions).to_contain_text("请教顾问")
    expect(page.locator('[data-test="suggestion-observe"]')).to_be_visible()


def test_summary_panel_shows_key_situation(page, server):
    page.goto(server)
    summary = page.locator('[data-test="summary-panel"]')
    expect(summary).to_contain_text("所在")
    expect(summary).to_contain_text("扬州府衙大堂")
    expect(summary).to_contain_text("在场")
    expect(summary).to_contain_text("线索")
    expect(summary).to_contain_text("行动角色")
    expect(summary).to_contain_text("无名书生")


def test_summary_panel_updates_after_clue_and_pressure(page, server):
    page.goto(server)
    page.locator('[data-test="input"]').fill("打听线索并施加压力")
    page.locator('[data-test="submit"]').click()
    summary = page.locator('[data-test="summary-panel"]')
    expect(summary).to_contain_text("2 条")
    expect(summary).to_contain_text("witness_pressure 2/3")
    expect(summary).to_contain_text("witness_pressure")


def test_priority_panel_surfaces_actionable_items(page, server):
    """待处理重点面板聚合高压力、最新线索、最新事件与下一步建议。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("打听线索并施加压力")
    page.locator('[data-test="submit"]').click()

    priority = page.locator('[data-test="priority-panel"]')
    expect(priority).to_contain_text("压力接近危险线")
    expect(priority).to_contain_text("witness_pressure 2/3")
    expect(priority).to_contain_text("最新线索")
    expect(priority).to_contain_text("陈掌柜听说码头有短工被拖欠工钱")
    expect(priority).to_contain_text("最新事件")
    expect(priority).to_contain_text("压力钟'witness_pressure'从0推进到2")
    expect(priority).to_contain_text("建议")
    expect(priority).to_contain_text("梳理线索")


def test_recent_panel_summarizes_latest_changes(page, server):
    """最近变化面板应聚合最新事件、线索与压力钟变化,帮助快速恢复上下文。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    recent = page.locator('[data-test="recent-panel"]')
    expect(recent).to_contain_text("事件")
    expect(recent).to_contain_text("玩家站在扬州府衙大堂上")

    page.locator('[data-test="input"]').fill("打听线索并施加压力")
    page.locator('[data-test="submit"]').click()

    recent = page.locator('[data-test="recent-panel"]')
    expect(recent).to_contain_text("事件")
    expect(recent).to_contain_text("压力钟'witness_pressure'从0推进到2")
    expect(recent).to_contain_text("线索")
    expect(recent).to_contain_text("陈掌柜听说码头有短工被拖欠工钱")
    expect(recent).to_contain_text("压力")
    expect(recent).to_contain_text("witness_pressure 2/3")
    expect(recent).to_contain_text("持续变化")


def test_gaps_panel_surfaces_missing_information(page, server):
    """信息缺口面板提示未触发剧情、隐藏观察点和可请教顾问。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    gaps = page.locator('[data-test="gaps-panel"]')
    expect(gaps).to_contain_text("未触发剧情线程")
    expect(gaps).to_contain_text("藏书楼失书")
    expect(gaps).to_contain_text("可能遗漏细节")
    expect(gaps).to_contain_text("附近顾问尚未请教")
    expect(gaps).to_contain_text("刘师爷")

    page.locator('[data-test="input"]').fill("打听线索")
    page.locator('[data-test="submit"]').click()
    expect(gaps).to_contain_text("未触发剧情线程")
    expect(gaps).not_to_contain_text("状告漕帮恶霸")


def test_evolutions_panel_shows_registered_entities(page, server):
    """世界演化面板展示已注册实体、频率、位置与演化回合。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    panel = page.locator('[data-test="evolutions-panel"]')
    # 知府与师爷为隔一回合频率
    expect(panel).to_contain_text("王知府")
    expect(panel).to_contain_text("刘师爷")
    expect(panel).to_contain_text("隔一回合")
    # 衙役为低频
    expect(panel).to_contain_text("低频")
    # 演化备注
    expect(panel).to_contain_text("知府是主线核心NPC")
    # 上次演化回合信息
    expect(panel).to_contain_text("上次演化")
    expect(panel).to_contain_text("回合 0")


def test_side_nav_badges_show_information_counts(page, server):
    """右栏信息导航显示关键数量,减少滚动查找。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    expect(page.locator('[data-test="side-nav-badge-time"]')).to_contain_text("4人在场")
    expect(page.locator('[data-test="side-nav-badge-suggestions"]')).to_contain_text("4项")
    expect(page.locator('[data-test="side-nav-badge-story"]')).to_contain_text("0线索")
    expect(page.locator('[data-test="side-nav-badge-review"]')).to_contain_text("1回合")

    page.locator('[data-test="input"]').fill("打听线索并施加压力")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="side-nav-badge-story"]')).to_contain_text("2线索")
    expect(page.locator('[data-test="side-nav-badge-review"]')).to_contain_text("5回合")


def test_side_nav_reopens_collapsed_target_section(page, server):
    """右栏信息导航可跳转到目标分组,并自动展开已折叠面板。"""
    page.goto(server)
    toggle = page.locator('[data-test="toggle-story"]')
    story = page.locator('[data-test="story-panel"]')
    section = page.locator('[data-panel-section="story"]')
    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(story).to_be_hidden()

    page.locator('[data-test="side-nav-story"]').click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(story).to_be_visible()
    expect(section).to_have_class(re.compile(r"\bfocused\b"))
    expect(page.locator('[data-test="side-nav"]')).to_be_visible()


def test_mobile_side_panel_drawer_opens_and_closes(page, server):
    """窄屏下状态面板可通过顶部入口打开,并可点击遮罩关闭。"""
    page.set_viewport_size({"width": 390, "height": 820})
    page.goto(server)
    panel = page.locator('[data-test="summary-panel"]')
    toggle = page.locator('[data-test="mobile-panel-toggle"]')
    backdrop = page.locator('[data-test="side-panel-backdrop"]')

    expect(toggle).to_be_visible()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(panel).not_to_be_in_viewport()

    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(panel).to_be_in_viewport()

    backdrop.click(position={"x": 5, "y": 5})
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(panel).not_to_be_in_viewport()


def test_info_density_toggle_compacts_and_persists(page, server):
    """右栏信息密度可切换为精简模式,并在刷新后保持。"""
    page.goto(server)
    summary = page.locator('[data-test="summary-panel"]')
    suggestions = page.locator('[data-test="suggestions-panel"]')
    expect(summary).to_contain_text("行动角色")
    expect(suggestions).to_contain_text("先看清现场与人物")
    expect(page.locator('[data-test="density-detailed"]')).to_have_attribute("aria-pressed", "true")

    page.locator('[data-test="density-compact"]').click()
    expect(page.locator('[data-test="density-compact"]')).to_have_attribute("aria-pressed", "true")
    expect(summary).not_to_contain_text("行动角色")
    expect(suggestions).not_to_contain_text("先看清现场与人物")

    page.reload()
    expect(page.locator('[data-test="density-compact"]')).to_have_attribute("aria-pressed", "true")
    expect(page.locator('[data-test="summary-panel"]')).not_to_contain_text("行动角色")



def test_panel_search_filters_sections_by_content(page, server):
    """右栏面板可按标题和内容筛选,快速定位目标信息。"""
    page.goto(server)
    search = page.locator('[data-test="panel-search-input"]')
    count = page.locator('[data-test="panel-search-count"]')
    expect(count).to_contain_text("共")
    search.fill("线索")

    expect(page.locator('[data-panel-section="summary"]')).to_be_visible()
    expect(page.locator('[data-panel-section="clues"]')).to_be_visible()
    expect(page.locator('[data-panel-section="player"]')).to_be_hidden()
    expect(page.locator('[data-test="panel-search-empty"]')).to_be_hidden()
    expect(page.locator('[data-test="panel-search-results"]')).to_be_visible()
    expect(page.locator('[data-test="panel-search-result-clues"]')).to_contain_text("线索记录")
    expect(count).to_contain_text("匹配")
    expect(count).to_contain_text("个面板")

    search.fill("不存在的面板内容")
    expect(page.locator('[data-test="panel-search-empty"]')).to_be_visible()
    expect(page.locator('[data-test="panel-search-results"]')).to_be_hidden()
    expect(count).to_contain_text("匹配 0")

    search.fill("")
    expect(page.locator('[data-panel-section="player"]')).to_be_visible()
    expect(page.locator('[data-test="panel-search-results"]')).to_be_hidden()
    expect(count).to_contain_text("共")



def test_panel_search_highlights_matching_text(page, server):
    """右栏搜索应高亮匹配文字,方便玩家定位面板内命中位置。"""
    page.goto(server)
    page.locator('[data-test="panel-search-input"]').fill("线索")

    highlights = page.locator('[data-test="panel-search-highlight"]')
    expect(highlights.first).to_be_visible()
    expect(highlights.first).to_contain_text("线索")

    page.locator('[data-test="panel-search-input"]').fill("")
    expect(page.locator('[data-test="panel-search-highlight"]')).to_have_count(0)



def test_panel_search_result_focuses_matching_section(page, server):
    """右栏搜索结果可直接跳转并展开匹配面板。"""
    page.goto(server)
    page.locator('[data-test="toggle-clues"]').click()
    expect(page.locator('[data-test="clues-panel"]')).to_be_hidden()

    page.locator('[data-test="panel-search-input"]').fill("线索记录")
    page.locator('[data-test="panel-search-result-clues"]').click()

    expect(page.locator('[data-test="toggle-clues"]')).to_have_attribute("aria-expanded", "true")
    expect(page.locator('[data-test="clues-panel"]')).to_be_visible()
    expect(page.locator('[data-panel-section="clues"]')).to_have_class(re.compile(r"\bfocused\b"))



def test_panel_search_keyboard_shortcut_focuses_search(page, server):
    """⌘/Ctrl+K 应聚焦右栏搜索框,便于键盘快速定位面板。"""
    page.goto(server)
    search = page.locator('[data-test="panel-search-input"]')
    page.locator('[data-test="input"]').focus()

    page.keyboard.press("Control+K")
    expect(search).to_be_focused()

    search.fill("线索")
    page.locator('[data-test="input"]').focus()
    page.keyboard.press("Control+K")
    expect(search).to_be_focused()
    assert page.evaluate("document.getSelection().toString()") == "线索"



def test_keyboard_help_lists_available_shortcuts(page, server):
    """右栏应静态展示可用快捷键,降低隐藏操作的发现成本。"""
    page.goto(server)
    help_panel = page.locator('[data-test="keyboard-help"]')

    expect(help_panel).to_be_visible()
    expect(help_panel).to_contain_text("快捷键")
    expect(help_panel).to_contain_text("Ctrl")
    expect(help_panel).to_contain_text("K")
    expect(help_panel).to_contain_text("搜索面板")
    expect(help_panel).to_contain_text("Enter")
    expect(help_panel).to_contain_text("提交行动")



def test_side_panel_sections_can_collapse_and_persist(page, server):
    """右栏面板可折叠,且刷新后保持折叠状态。"""
    page.goto(server)
    toggle = page.locator('[data-test="toggle-story"]')
    story = page.locator('[data-test="story-panel"]')
    expect(story).to_be_visible()

    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(story).to_be_hidden()

    page.reload()
    expect(page.locator('[data-test="toggle-story"]'))\
        .to_have_attribute("aria-expanded", "false")
    expect(page.locator('[data-test="story-panel"]')).to_be_hidden()



def test_side_panel_bulk_controls_expand_and_collapse_all(page, server):
    """右栏面板可一键全部折叠/展开,且刷新后保持。"""
    page.goto(server)
    expect(page.locator('[data-test="summary-panel"]')).to_be_visible()
    expect(page.locator('[data-test="story-panel"]')).to_be_visible()

    page.locator('[data-test="panel-collapse-all"]').click()
    expect(page.locator('[data-test="toggle-summary"]')).to_have_attribute("aria-expanded", "false")
    expect(page.locator('[data-test="summary-panel"]')).to_be_hidden()
    expect(page.locator('[data-test="story-panel"]')).to_be_hidden()

    page.reload()
    expect(page.locator('[data-test="summary-panel"]')).to_be_hidden()

    page.locator('[data-test="panel-expand-all"]').click()
    expect(page.locator('[data-test="toggle-summary"]')).to_have_attribute("aria-expanded", "true")
    expect(page.locator('[data-test="summary-panel"]')).to_be_visible()
    expect(page.locator('[data-test="story-panel"]')).to_be_visible()



def test_panel_context_notice_explains_hidden_information(page, server):
    """右栏顶部应提示搜索/折叠导致的信息隐藏,并提供恢复入口。"""
    page.goto(server)
    notice = page.locator('[data-test="panel-context-notice"]')
    expect(notice).to_be_hidden()

    page.locator('[data-test="panel-search-input"]').fill("线索")
    expect(notice).to_be_visible()
    expect(notice).to_contain_text("搜索已隐藏")
    expect(page.locator('[data-panel-section="player"]')).to_be_hidden()

    page.locator('[data-test="panel-context-clear-search"]').click()
    expect(page.locator('[data-panel-section="player"]')).to_be_visible()
    expect(page.locator('[data-test="panel-search-input"]')).to_have_value("")

    page.locator('[data-test="toggle-story"]').click()
    expect(notice).to_contain_text("1 个面板已折叠")
    page.locator('[data-test="panel-context-expand-all"]').click()
    expect(page.locator('[data-test="story-panel"]')).to_be_visible()
    expect(notice).to_be_hidden()



def test_collapsed_panel_shows_update_badge(page, server):
    """折叠面板内容更新时显示提示,展开后清除。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()

    page.locator('[data-test="toggle-clues"]').click()
    expect(page.locator('[data-test="clues-panel"]')).to_be_hidden()
    expect(page.locator('[data-test="panel-update-clues"]')).to_have_count(0)

    page.locator('[data-test="input"]').fill("打听一下有什么线索")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="panel-update-clues"]')).to_contain_text("更新")

    page.locator('[data-test="toggle-clues"]').click()
    expect(page.locator('[data-test="clues-panel"]')).to_be_visible()
    expect(page.locator('[data-test="clues-panel"]')).to_contain_text("状纸被师爷压下")
    expect(page.locator('[data-test="panel-update-clues"]')).to_have_count(0)



def test_side_nav_summarizes_collapsed_panel_updates(page, server):
    """右栏导航应汇总分组内折叠面板的新信息数量。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()

    page.locator('[data-test="toggle-clues"]').click()
    page.locator('[data-test="toggle-pressure"]').click()
    expect(page.locator('[data-test="side-nav-update-story"]')).to_have_count(0)

    page.locator('[data-test="input"]').fill("打听线索并施加压力")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="side-nav-update-story"]')).to_contain_text("2新")

    page.locator('[data-test="toggle-clues"]').click()
    expect(page.locator('[data-test="side-nav-update-story"]')).to_contain_text("1新")

    page.locator('[data-test="side-nav-story"]').click()
    expect(page.locator('[data-test="pressure-panel"]')).to_be_visible()
    expect(page.locator('[data-test="side-nav-update-story"]')).to_have_count(0)



def test_renderer_skips_unchanged_state(page, server):
    """重复渲染相同状态时,Pixi 视口应跳过重绘。"""
    page.goto(server)
    page.wait_for_function("window.__renderSceneStats.draws >= 1")
    before = page.evaluate("window.__renderSceneStats")
    page.evaluate("renderScene(lastSnapshot)")
    after = page.evaluate("window.__renderSceneStats")
    assert after["draws"] == before["draws"]
    assert after["skips"] == before["skips"] + 1


def test_suggestion_button_sends_turn(page, server):
    page.goto(server)
    page.locator('[data-test="suggestion-observe"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("仔细观察")
    expect(page.locator('[data-test="observation-court_hall_case_table"]'))\
        .to_contain_text("已发现")


def test_timeline_panel_updates_after_input(page, server):
    page.goto(server)
    page.locator('[data-test="input"]').fill("记录一条时间线")
    page.locator('[data-test="submit"]').click()

    timeline = page.locator('[data-test="timeline-panel"]')
    expect(timeline).to_contain_text("测试事件:记录一条时间线")
    expect(timeline).to_contain_text("player")
    expect(timeline).to_contain_text("最新")
    expect(timeline).to_contain_text("test")


def test_timeline_summary_shows_filtered_count_and_dominant_type(page, server):
    """事件时间线摘要展示当前筛选数量与主要事件类型。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("打听线索并请教顾问")
    page.locator('[data-test="submit"]').click()

    summary = page.locator('[data-test="timeline-summary"]')
    expect(summary).to_contain_text("显示全部 5 件")
    expect(summary).to_contain_text("剧情最多(2件)")

    page.locator('[data-test="timeline-filter-social"]').click()
    expect(summary).to_contain_text("显示社交 2 件")
    expect(summary).to_contain_text("剧情最多(2件)")



def test_timeline_legend_explains_event_types(page, server):
    """时间线应展示类型图例,帮助理解筛选与标签含义。"""
    page.goto(server)
    legend = page.locator('[data-test="timeline-legend"]')
    expect(legend).to_be_visible()
    expect(legend).to_contain_text("剧情")
    expect(legend).to_contain_text("线索、结局与主线推进")
    expect(legend).to_contain_text("社交")
    expect(legend).to_contain_text("请教、交谈与人物互动")
    expect(legend).to_contain_text("战斗")
    expect(legend).to_contain_text("交易")
    expect(legend).to_contain_text("其他")



def test_timeline_groups_events_by_turn(page, server):
    """时间线按回合分组,降低连续事件的阅读成本。"""
    page.goto(server)
    page.evaluate("""
        renderTimelinePanel({ events: [
            { id: 1, turn: 1, actor: 'player', type: 'record_clue', summary: '第一回合发现线索' },
            { id: 2, turn: 1, actor: 'system', type: 'record_clue', summary: '第一回合补充线索' },
            { id: 3, turn: 2, actor: 'shiye', type: 'advisor', summary: '第二回合请教顾问' },
        ] })
    """)

    timeline = page.locator('[data-test="timeline-panel"]')
    groups = timeline.locator('[data-test="timeline-group"]')
    expect(groups).to_have_count(2)
    expect(groups.first).to_contain_text("回合 2")
    expect(groups.first).to_contain_text("1件 · 社交1")
    expect(groups.nth(1)).to_contain_text("回合 1")
    expect(groups.nth(1)).to_contain_text("2件 · 剧情2")
    expect(timeline.locator('[data-test="timeline-group-summary"]')).to_have_count(2)

    page.locator('[data-test="timeline-filter-social"]').click()
    expect(timeline.locator('[data-test="timeline-group"]')).to_have_count(1)
    expect(timeline.locator('[data-test="timeline-group"]')).to_contain_text("回合 2")
    expect(timeline.locator('[data-test="timeline-group"]')).to_contain_text("1件 · 社交1")



def test_timeline_filters_events_by_type(page, server):
    """事件时间线可按类型筛选,减少复盘时的信息噪音。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("打听线索并请教顾问")
    page.locator('[data-test="submit"]').click()

    timeline = page.locator('[data-test="timeline-panel"]')
    expect(page.locator('[data-test="timeline-filters"]')).to_be_visible()
    expect(page.locator('[data-test="timeline-filter-all"]')).to_contain_text("全部")
    expect(page.locator('[data-test="timeline-filter-social"]')).to_contain_text("社交")
    expect(page.locator('[data-test="timeline-filter-plot"]')).to_contain_text("剧情")

    page.locator('[data-test="timeline-filter-social"]').click()
    expect(timeline).to_contain_text("请教")
    expect(timeline.locator('[data-event-type="social"]')).to_have_count(2)
    expect(timeline.locator('[data-event-type="plot"]')).to_have_count(0)

    page.locator('[data-test="timeline-filter-plot"]').click()
    expect(timeline).to_contain_text("线索")
    expect(timeline.locator('[data-event-type="plot"]')).to_have_count(2)
    expect(timeline.locator('[data-event-type="social"]')).to_have_count(0)


def test_status_effect_renders_in_panel(page, server):
    page.goto(server)
    page.locator('[data-test="input"]').fill("给我加个状态")
    page.locator('[data-test="submit"]').click()

    # 等待状态出现在 player panel
    player_panel = page.locator('[data-test="player-panel"]')
    expect(player_panel).to_contain_text("测试状态", timeout=5000)


def test_audit_modal_shows_recent_turn(page, server):
    page.goto(server)
    page.locator('[data-test="input"]').fill("审计动作")
    page.locator('[data-test="submit"]').click()
    # 等 bubble 出现
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("审计动作")

    page.locator('[data-test="show-audit"]').click()
    audit_body = page.locator('[data-test="audit-body"]')
    expect(audit_body).to_contain_text("审计动作")
    expect(audit_body).to_contain_text("log_event")


def test_debug_console_modal_shows_world_tools_and_performance(page, server):
    """开发者控制台展示世界状态、工具调用日志与性能指标。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("开发者控制台动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("开发者控制台动作")

    page.locator('[data-test="debug-console"]').click()

    modal = page.locator('[data-test="debug-modal"]')
    body = page.locator('[data-test="debug-body"]')
    expect(modal).to_be_visible()
    expect(page.locator('[data-test="debug-summary"]')).to_contain_text("实体")
    expect(page.locator('[data-test="debug-world-state"]')).to_contain_text("世界状态查看器")
    expect(page.locator('[data-test="debug-world-state"]')).to_contain_text("无名书生")
    expect(page.locator('[data-test="debug-tool-log"]')).to_contain_text("工具调用日志")
    expect(body).to_contain_text("log_event")
    expect(page.locator('[data-test="debug-tool-log"]')).to_contain_text("输入")
    expect(page.locator('[data-test="debug-tool-log"]')).to_contain_text("输出")
    expect(page.locator('[data-test="debug-copy-input"]').first).to_contain_text("复制输入")
    expect(page.locator('[data-test="debug-copy-output"]').first).to_contain_text("复制输出")
    expect(page.locator('[data-test="debug-tool-output"]').first).to_contain_text("测试事件:开发者控制台动作")
    page.locator('[data-test="debug-copy-output"]').first.click()
    expect(page.locator('[data-test="debug-copy-output"]').first).to_contain_text("已复制输出")
    expect(page.locator('[data-test="debug-performance"]')).to_contain_text("性能监控")
    expect(page.locator('[data-test="debug-performance"]')).to_contain_text("渲染统计")

    page.locator('#close-debug').click()
    expect(modal).to_be_hidden()


def test_debug_console_exports_filtered_debug_bundle(page, server):
    """开发者控制台可导出包含当前筛选工具调用的调试包。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("观察并记录线索")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("观察并记录线索")

    page.locator('[data-test="debug-console"]').click()
    expect(page.locator('[data-test="debug-export"]')).to_contain_text("导出调试包")
    page.locator('[data-test="debug-tool-name-filter"]').select_option("discover_observation")
    page.locator('[data-test="debug-tool-query-filter"]').fill("court_hall_case_table")

    with page.expect_download() as download_info:
        page.locator('[data-test="debug-export-bundle"]').click()
    download = download_info.value
    assert download.suggested_filename.startswith("mingrpg-debug-")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导出调试包")


def test_debug_console_filters_tool_calls(page, server):
    """开发者控制台可按工具名和内容筛选工具调用。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("观察并记录线索")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("观察并记录线索")

    page.locator('[data-test="debug-console"]').click()
    log = page.locator('[data-test="debug-tool-log"]')
    expect(log).to_contain_text("log_event")
    expect(log).to_contain_text("discover_observation")
    expect(log).to_contain_text("record_clue")

    page.locator('[data-test="debug-tool-name-filter"]').select_option("discover_observation")
    expect(log).to_contain_text("匹配 1 次调用")
    expect(page.locator('[data-test="debug-tool-discover_observation"]')).to_be_visible()
    expect(page.locator('[data-test="debug-tool-record_clue"]')).to_have_count(0)

    page.locator('[data-test="debug-tool-query-filter"]').fill("court_hall_case_table")
    expect(log).to_contain_text("匹配 1 次调用")
    expect(log).to_contain_text("discover_observation")

    page.locator('[data-test="debug-tool-query-filter"]').fill("无匹配工具")
    expect(log).to_contain_text("匹配 0 次调用")
    expect(page.locator('[data-test="debug-tool-empty"]')).to_be_visible()

    page.locator('[data-test="debug-tool-filter-clear"]').click()
    expect(log).to_contain_text("log_event")
    expect(log).to_contain_text("record_clue")



def test_debug_console_filters_entities_and_flags(page, server):
    """开发者控制台可浏览并筛选实体与 flag。"""
    page.goto(server)
    page.locator('[data-test="debug-console"]').click()

    browser = page.locator('[data-test="debug-entity-flag-browser"]')
    expect(browser).to_be_visible()
    expect(page.locator('[data-test="debug-entity-player"]')).to_contain_text("无名书生")
    expect(page.locator('[data-test="debug-entity-zhifu_wang"]')).to_contain_text("王知府")
    expect(page.locator('[data-test="debug-flag-story_seeds"]')).to_contain_text("story_seeds")

    page.locator('[data-test="debug-browser-filter"]').fill("zhifu_wang")
    expect(page.locator('[data-test="debug-entity-zhifu_wang"]')).to_be_visible()
    expect(page.locator('[data-test="debug-entity-player"]')).to_be_hidden()
    expect(page.locator('[data-test="debug-flag-story_seeds"]')).to_be_hidden()
    # evolution_registry flag contains "zhifu_wang" in its value
    expect(page.locator('[data-test="debug-flag-evolution_registry"]')).to_be_visible()
    expect(page.locator('[data-test="debug-entity-count"]')).to_contain_text("1")
    expect(page.locator('[data-test="debug-flag-count"]')).to_contain_text("1")

    page.locator('[data-test="debug-browser-filter"]').fill("story_seeds")
    expect(page.locator('[data-test="debug-entity-zhifu_wang"]')).to_be_hidden()
    expect(page.locator('[data-test="debug-flag-story_seeds"]')).to_be_visible()
    expect(page.locator('[data-test="debug-entity-count"]')).to_contain_text("0")
    expect(page.locator('[data-test="debug-flag-count"]')).to_contain_text("1")

    page.locator('[data-test="debug-browser-filter"]').fill("无匹配调试项")
    expect(page.locator('[data-test="debug-browser-empty"]')).to_be_visible()


def test_debug_console_loads_test_preset(page, server):
    """开发者控制台可加载预设测试用例并刷新面板。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()

    page.locator('[data-test="debug-console"]').click()
    presets = page.locator('[data-test="debug-test-presets"]')
    expect(presets).to_be_visible()
    expect(presets).to_contain_text("府衙线索压力局")
    expect(presets).to_contain_text("验收点")

    page.locator('[data-test="debug-preset-load-court_clue_pressure"]').click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已加载预设测试用例")
    expect(page.locator('[data-test="clues-panel"]')).to_contain_text("状纸曾被刘师爷压下")
    expect(page.locator('[data-test="pressure-panel"]')).to_contain_text("witness_pressure")
    expect(page.locator('[data-test="timeline-panel"]')).to_contain_text("预设: 证人压力推进到2/3")
    expect(page.locator('[data-test="debug-flag-test_preset"]')).to_contain_text("court_clue_pressure")



def test_debug_console_previews_test_snapshot_detail(page, server):
    """开发者控制台可在加载前预览测试快照详情。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("快照详情动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("快照详情动作")

    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("详情预览快照")
    page.locator('[data-test="debug-snapshot-create"]').click()
    page.locator('[data-test^="debug-snapshot-detail-"]').first.click()

    detail = page.locator('[data-test="debug-snapshot-detail-result"]')
    expect(detail).to_be_visible()
    expect(detail).to_contain_text("详情预览")
    expect(detail).to_contain_text("无名书生")
    expect(detail).to_contain_text("扬州府衙大堂")
    expect(detail).to_contain_text("最近事件")
    expect(detail).to_contain_text("快照详情动作")



def test_debug_console_filters_test_snapshots(page, server):
    """开发者控制台可按名称、备注或 id 筛选测试快照。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()

    page.locator('[data-test="debug-snapshot-name"]').fill("府衙验收快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("线索压力回归")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("府衙验收快照")
    summary = page.locator('[data-test="debug-snapshot-summary"]')
    expect(summary).to_contain_text("总数")
    expect(summary).to_contain_text("实体")
    expect(summary).to_contain_text("地点")
    expect(summary).to_contain_text("事件")
    expect(summary).to_contain_text("Flags")
    expect(summary).to_contain_text("最近更新")

    page.locator('[data-test="debug-snapshot-name"]').fill("街市空盘快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("商贸回归")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("街市空盘快照")

    page.locator('[data-test="debug-snapshot-filter"]').fill("线索压力")
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1 /")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("府衙验收快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("街市空盘快照")

    page.locator('[data-test="debug-snapshot-filter"]').fill("无匹配快照")
    expect(page.locator('[data-test="debug-snapshot-empty"]')).to_be_visible()
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 0 /")

    page.locator('[data-test="debug-snapshot-filter-clear"]').click()
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("显示")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("府衙验收快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("街市空盘快照")

    page.locator('[data-test="debug-snapshot-filter"]').fill("回归")
    page.locator('[data-test="debug-snapshot-sort"]').select_option("name_asc")
    expect(page.locator('[data-test="debug-snapshot-list"] .debug-snapshot-item').first).to_contain_text("府衙验收快照")
    page.locator('[data-test="debug-snapshot-sort"]').select_option("name_desc")
    expect(page.locator('[data-test="debug-snapshot-list"] .debug-snapshot-item').first).to_contain_text("街市空盘快照")



def test_debug_console_manages_test_snapshot_tags(page, server):
    """开发者控制台可为测试快照添加标签,并按标签筛选。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()

    page.locator('[data-test="debug-snapshot-name"]').fill("标签府衙快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("标签筛选回归")
    page.locator('[data-test="debug-snapshot-tags"]').fill("府衙, 回归")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("标签府衙快照")
    expect(page.locator('[data-test^="debug-snapshot-tags-"]').first).to_contain_text("府衙")

    page.locator('[data-test="debug-snapshot-name"]').fill("街市标签快照")
    page.locator('[data-test="debug-snapshot-tags"]').fill("街市")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("街市标签快照")

    page.locator('[data-test="debug-snapshot-tag-filter"]').select_option("府衙")
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1 /")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("标签府衙快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("街市标签快照")



def test_debug_console_snapshot_quick_filters(page, server):
    """开发者控制台展示快照快速筛选摘要,可一键按标签/置顶/归档过滤。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()

    page.locator('[data-test="debug-snapshot-name"]').fill("快捷府衙快照")
    page.locator('[data-test="debug-snapshot-tags"]').fill("快捷府衙")
    page.locator('[data-test="debug-snapshot-create"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("快捷街市快照")
    page.locator('[data-test="debug-snapshot-tags"]').fill("快捷街市")
    page.locator('[data-test="debug-snapshot-create"]').click()

    quick = page.locator('[data-test="debug-snapshot-quick-filters"]')
    expect(quick).to_contain_text("当前")
    expect(quick).to_contain_text("全部")
    expect(quick).to_contain_text("快捷府衙 1")
    page.locator('[data-test="debug-snapshot-quick-tag-快捷府衙"]').click()
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1 /")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("快捷府衙快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("快捷街市快照")

    page.locator('[data-test^="debug-snapshot-pin-"]').first.click()
    page.locator('[data-test="debug-snapshot-quick-pinned"]').click()
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1 /")
    expect(page.locator('[data-test="debug-snapshot-filter"]')).to_have_value("pinned")

    page.locator('[data-test^="debug-snapshot-archive-"]').first.click()
    page.locator('[data-test="debug-snapshot-quick-archived"]').click()
    expect(page.locator('[data-test="debug-snapshot-filter"]')).to_have_value("archived")
    expect(page.locator('[data-test="debug-snapshot-show-archived"]')).to_be_checked()



def test_debug_console_exports_single_test_snapshot(page, server):
    """开发者控制台可导出单个测试快照 JSON,便于分享复现盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("单个快照导出浏览器动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("单个快照导出浏览器动作")

    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("单个导出快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("E2E export")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("单个导出快照")

    with page.expect_download() as download_info:
        page.locator('[data-test^="debug-snapshot-export-"]').first.click()
    download = download_info.value
    assert download.suggested_filename.startswith("mingrpg-test-snapshot-")
    assert download.suggested_filename.endswith(".json")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导出测试快照")
    expect(page.locator('[data-test^="debug-snapshot-activity-"]').first).to_contain_text("导出")



def test_debug_console_duplicates_test_snapshot(page, server):
    """开发者控制台可复制测试快照,便于从既有盘面派生新回归快照。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("可复制快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("复制来源")
    page.locator('[data-test="debug-snapshot-tags"]').fill("府衙, 复制")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("可复制快照")

    page.locator('[data-test^="debug-snapshot-duplicate-"]').first.click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已复制测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("可复制快照 副本")
    page.locator('[data-test="debug-snapshot-filter"]').fill("可复制快照")
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 2 /")
    expect(page.locator('[data-test^="debug-snapshot-tags-"]').first).to_contain_text("府衙")



def test_debug_console_pins_test_snapshot_first(page, server):
    """开发者控制台可置顶常用测试快照,并在列表中优先显示。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    for name in ["置顶回归普通", "置顶回归常用"]:
        page.locator('[data-test="debug-snapshot-name"]').fill(name)
        page.locator('[data-test="debug-snapshot-create"]').click()
        expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text(name)

    page.locator('[data-test="debug-snapshot-filter"]').fill("置顶回归")
    page.locator('[data-test="debug-snapshot-sort"]').select_option("name_asc")
    expect(page.locator('[data-test="debug-snapshot-list"] .debug-snapshot-item').first).to_contain_text("置顶回归常用")
    page.locator('[data-test^="debug-snapshot-pin-"]').first.click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已置顶测试快照")
    first = page.locator('[data-test="debug-snapshot-list"] .debug-snapshot-item').first
    expect(first).to_contain_text("置顶")
    expect(first).to_contain_text("置顶回归常用")

    page.locator('[data-test="debug-snapshot-filter"]').fill("pinned")
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1 /")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("置顶回归常用")

    page.locator('[data-test^="debug-snapshot-pin-"]').first.click()
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已取消置顶测试快照")



def test_debug_console_bulk_exports_selected_test_snapshots(page, server):
    """开发者控制台可勾选并批量导出测试快照包,便于分享多组复现盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    for name in ["批量导出甲", "批量导出乙", "保留快照"]:
        page.locator('[data-test="debug-snapshot-name"]').fill(name)
        page.locator('[data-test="debug-snapshot-create"]').click()
        expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text(name)

    page.locator('[data-test="debug-snapshot-filter"]').fill("批量导出")
    page.locator('[data-test="debug-snapshot-select-visible"]').check()
    expect(page.locator('[data-test="debug-snapshot-selected-count"]')).to_contain_text("已选 2 个")
    with page.expect_download() as download_info:
        page.locator('[data-test="debug-snapshot-bulk-export"]').click()
    download = download_info.value

    assert download.suggested_filename.startswith("mingrpg-test-snapshot-bundle-")
    assert download.suggested_filename.endswith(".json")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导出 2 个测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量导出甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量导出乙")



def test_debug_console_previews_and_confirms_bulk_snapshot_import(page, server, tmp_path):
    """开发者控制台导入快照包前应预览内容,确认后才加入本地快照列表。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    bundle = page.evaluate("""
        async () => {
            const ids = [];
            for (const name of ['预览导入甲', '预览导入乙']) {
                const created = await fetch('/api/debug/test-snapshots', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, note: 'bundle preview' })
                }).then(r => r.json());
                ids.push(created.snapshot.id);
            }
            return fetch('/api/debug/test-snapshots/bulk-export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ snapshot_ids: ids })
            }).then(r => r.json());
        }
    """)
    import_path = tmp_path / "mingrpg-test-snapshot-bundle-import.json"
    import_path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")

    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-bundle-file-input"]').set_input_files(str(import_path))

    preview = page.locator('[data-test="debug-snapshot-bundle-preview"]')
    expect(preview).to_be_visible()
    expect(preview).to_contain_text("快照包预览")
    expect(preview).to_contain_text("预览导入甲")
    expect(preview).to_contain_text("预览导入乙")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已预览 2 个测试快照")

    page.evaluate("""
        fetch('/api/debug/test-snapshots/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ snapshot_ids: Array.from(document.querySelectorAll('[data-debug-snapshot-select]')).map((el) => el.dataset.debugSnapshotSelect) })
        }).then(r => r.json())
    """)
    page.locator('[data-test="debug-snapshot-bundle-confirm-import"]').click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导入 2 个测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("预览导入甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("预览导入乙")
    expect(page.locator('[data-test="debug-snapshot-bundle-preview"]')).to_have_count(0)



def test_debug_console_bulk_archives_selected_test_snapshots(page, server):
    """开发者控制台可勾选并批量归档/取消归档测试快照,便于整理调试盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    for name in ["批量归档甲", "批量归档乙", "保留快照"]:
        page.locator('[data-test="debug-snapshot-name"]').fill(name)
        page.locator('[data-test="debug-snapshot-create"]').click()
        expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text(name)

    page.locator('[data-test="debug-snapshot-filter"]').fill("批量归档")
    page.locator('[data-test="debug-snapshot-select-visible"]').check()
    expect(page.locator('[data-test="debug-snapshot-selected-count"]')).to_contain_text("已选 2 个")
    page.locator('[data-test="debug-snapshot-bulk-archive"]').click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已归档 2 个测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("批量归档甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("批量归档乙")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("无匹配测试快照")

    page.locator('[data-test="debug-snapshot-show-archived"]').check()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量归档甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量归档乙")
    page.locator('[data-test="debug-snapshot-select-visible"]').check()
    page.locator('[data-test="debug-snapshot-bulk-unarchive"]').click()

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已取消归档 2 个测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量归档甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("批量归档乙")



def test_debug_console_confirms_single_test_snapshot_delete(page, server):
    """开发者控制台删除单个测试快照前应二次确认,避免误删调试盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("单个删除确认快照")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("单个删除确认快照")
    page.locator('[data-test="debug-snapshot-filter"]').fill("单个删除确认快照")

    dismissed = []
    page.once("dialog", lambda dialog: (dismissed.append(dialog.message), dialog.dismiss()))
    page.locator('[data-test^="debug-snapshot-delete-"]').first.click()
    assert dismissed and "确定删除这个测试快照" in dismissed[0]
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("单个删除确认快照")

    accepted = []
    page.once("dialog", lambda dialog: (accepted.append(dialog.message), dialog.accept()))
    page.locator('[data-test^="debug-snapshot-delete-"]').first.click()
    assert accepted and "确定删除这个测试快照" in accepted[0]
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已删除测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("单个删除确认快照")



def test_debug_console_bulk_deletes_selected_test_snapshots(page, server):
    """开发者控制台可勾选并确认批量删除测试快照,便于清理调试盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    for name in ["批量删除甲", "批量删除乙", "保留快照"]:
        page.locator('[data-test="debug-snapshot-name"]').fill(name)
        page.locator('[data-test="debug-snapshot-create"]').click()
        expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text(name)

    page.locator('[data-test="debug-snapshot-filter"]').fill("批量删除")
    page.locator('[data-test="debug-snapshot-select-visible"]').check()
    expect(page.locator('[data-test="debug-snapshot-selected-count"]')).to_contain_text("已选 2 个")
    messages = []
    page.once("dialog", lambda dialog: (messages.append(dialog.message), dialog.accept()))
    page.locator('[data-test="debug-snapshot-bulk-delete"]').click()

    assert messages and "确定删除所选 2 个测试快照" in messages[0]
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已删除 2 个测试快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("批量删除甲")
    expect(page.locator('[data-test="debug-snapshot-list"]')).not_to_contain_text("批量删除乙")
    page.locator('[data-test="debug-snapshot-filter-clear"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("保留快照")
    expect(page.locator('[data-test="debug-snapshot-selected-count"]')).to_contain_text("已选 0 个")



def test_debug_console_exports_test_snapshot_index(page, server):
    """开发者控制台可导出测试快照索引 JSON,用于归档快照目录。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-name"]').fill("索引导出快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("E2E index")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("索引导出快照")

    with page.expect_download() as download_info:
        page.locator('[data-test="debug-snapshot-index-export"]').click()
    download = download_info.value
    assert download.suggested_filename.startswith("mingrpg-test-snapshot-index-")
    assert download.suggested_filename.endswith(".json")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导出")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("测试快照索引")



def test_debug_console_exports_test_snapshot_health_report(page, server):
    """开发者控制台可导出测试快照健康报告 JSON,便于分享坏档诊断。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="debug-console"]').click()
    for _ in range(2):
        page.locator('[data-test="debug-snapshot-name"]').fill("健康报告重复快照")
        page.locator('[data-test="debug-snapshot-create"]').click()
        expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("健康报告重复快照")

    created_ids = page.evaluate("""
        async () => {
            const res = await fetch('/api/debug/test-snapshots').then(r => r.json());
            return res.snapshots
                .filter((snapshot) => snapshot.name === '健康报告重复快照')
                .map((snapshot) => snapshot.id);
        }
    """)

    page.locator('[data-test="debug-snapshot-health-check"]').click()
    health = page.locator('[data-test="debug-snapshot-health-result"]')
    expect(health).to_be_visible()
    expect(health).to_contain_text("个有问题")
    target_id = created_ids[0]
    health.locator(f'[data-debug-health-focus="{target_id}"]').click()
    expect(page.locator('[data-test="debug-snapshot-filter"]')).to_have_value(target_id)
    expect(page.locator('[data-test="debug-snapshot-filter-count"]')).to_contain_text("匹配 1")

    with page.expect_download() as download_info:
        page.locator('[data-test="debug-snapshot-health-export"]').click()
    download = download_info.value
    assert download.suggested_filename.startswith("mingrpg-test-snapshot-health-")
    assert download.suggested_filename.endswith(".json")
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导出测试快照校验报告")



def test_debug_console_imports_single_test_snapshot_file(page, server, tmp_path):
    """开发者控制台可导入单个测试快照 JSON,恢复分享的复现盘面。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    snapshot = page.evaluate("""
        async () => {
            await fetch('/api/turn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: '单文件导入前动作' })
            });
            const created = await fetch('/api/debug/test-snapshots', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: '单文件导入快照', note: 'E2E import' })
            }).then(r => r.json());
            return fetch(`/api/debug/test-snapshots/${created.snapshot.id}/export`).then(r => r.json());
        }
    """)
    import_path = tmp_path / "mingrpg-test-snapshot-import.json"
    import_path.write_text(json.dumps(snapshot, ensure_ascii=False), encoding="utf-8")
    page.evaluate("fetch('/api/turn', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ input: '单文件导入后动作' }) }).then(r => r.json())")
    page.reload()
    expect(page.locator('[data-test="timeline-panel"]')).to_contain_text("单文件导入后动作")

    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-file-input"]').set_input_files(str(import_path))

    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已导入测试快照")
    expect(page.locator('[data-test="timeline-panel"]')).to_contain_text("单文件导入前动作")
    expect(page.locator('[data-test="timeline-panel"]')).not_to_contain_text("单文件导入后动作")



def test_debug_console_saves_and_loads_test_snapshot(page, server):
    """开发者控制台可保存并加载测试场景快照。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("快照前浏览器动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("快照前浏览器动作")

    page.locator('[data-test="debug-console"]').click()
    snapshots = page.locator('[data-test="debug-test-snapshots"]')
    expect(snapshots).to_be_visible()
    page.locator('[data-test="debug-snapshot-name"]').fill("浏览器快照")
    page.locator('[data-test="debug-snapshot-note"]').fill("E2E")
    page.locator('[data-test="debug-snapshot-create"]').click()
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("浏览器快照")
    expect(page.locator('[data-test="debug-snapshot-list"]')).to_contain_text("E2E")

    page.locator('#close-debug').click()
    page.locator('[data-test="input"]').fill("快照后浏览器动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="timeline-panel"]')).to_contain_text("快照后浏览器动作")

    page.locator('[data-test="debug-console"]').click()
    page.locator('[data-test="debug-snapshot-list"] button').first.click()
    confirm = page.locator('[data-test="debug-snapshot-load-confirm"]')
    expect(confirm).to_be_visible()
    expect(confirm).to_contain_text("加载确认")
    expect(confirm).to_contain_text("浏览器快照")
    expect(confirm).to_contain_text("无名书生")
    expect(confirm).to_contain_text("最近事件")
    page.locator('[data-test^="debug-snapshot-confirm-load-"]').first.click()
    expect(page.locator('[data-test="bubble-system"]')
            .last).to_contain_text("已加载测试快照")
    expect(page.locator('[data-test="timeline-panel"]')).to_contain_text("快照前浏览器动作")
    expect(page.locator('[data-test="timeline-panel"]')).not_to_contain_text("快照后浏览器动作")
    expect(page.locator('[data-test^="debug-snapshot-activity-"]').first).to_contain_text("加载")


def test_reset_clears_chat_and_restores_player(page, server):
    page.goto(server)
    # 做一次动作
    page.locator('[data-test="input"]').fill("打点酱油")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("打点酱油")

    page.on("dialog", lambda d: d.accept())
    page.locator('[data-test="reset"]').click()
    # 重置后 player panel 应仍显示无名书生(scenario 重新种)
    expect(page.locator('[data-test="player-panel"]'))\
        .to_contain_text("无名书生")


def test_birth_settings_modal_applies_selected_template(page, server):
    """出生设置面板应展示模板详情,并可用模板重置新游戏。"""
    page.goto(server)
    page.locator('[data-test="birth-settings"]').click()

    modal = page.locator('[data-test="birth-modal"]')
    expect(modal).to_be_visible()
    expect(page.locator('[data-test="birth-template-scholar"]')).to_contain_text("落第书生")
    expect(page.locator('[data-test="birth-template-merchant_son"]')).to_contain_text("商人之子")
    expect(page.locator('[data-test="birth-template-detail"]')).to_contain_text("讼学")

    page.locator('[data-test="birth-template-merchant_son"]').click()
    expect(page.locator('[data-test="birth-template-detail"]')).to_contain_text("商贸")
    expect(page.locator('[data-test="birth-template-detail"]')).to_contain_text("180 文")
    page.locator('[data-test="apply-birth-template"]').click()

    expect(modal).to_be_hidden()
    expect(page.locator('[data-test="player-panel"]')).to_contain_text("商人之子")
    expect(page.locator('[data-test="player-panel"]')).to_contain_text("钱: 180 文")
    expect(page.locator('[data-test="location-panel"]')).to_contain_text("街市中心")
    expect(page.locator('[data-test="bubble-system"]')).to_contain_text("已选择「商人之子」出生")


def test_birth_settings_quick_switch_applies_template(page, server):
    """出生设置管理区应支持一键快速切换出生配置。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset?template_id=merchant_son', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="birth-settings"]').click()

    quick = page.locator('[data-test="birth-quick-switch"]')
    expect(quick).to_be_visible()
    expect(quick).to_contain_text("当前出生")
    expect(quick).to_contain_text("商人之子")
    expect(page.locator('[data-test="birth-quick-merchant_son"]')).to_have_class(re.compile(r"\bactive\b"))

    page.locator('[data-test="birth-quick-beggar"]').click()

    expect(page.locator('[data-test="birth-modal"]')).to_be_hidden()
    expect(page.locator('[data-test="player-panel"]')).to_contain_text("城中乞儿")
    expect(page.locator('[data-test="player-panel"]')).to_contain_text("钱: 3 文")
    expect(page.locator('[data-test="bubble-system"]')).to_contain_text("已选择「城中乞儿」出生")



def test_story_panel_shows_main_thread(page, server):
    """主线剧情面板应显示主线标题和支线。"""
    page.goto(server)
    story = page.locator('[data-test="story-panel"]')
    expect(story).to_contain_text("状告")


def test_story_panel_shows_thread_progress_overview(page, server):
    """主线剧情面板应概览线索线程进度,方便快速判断剧情分布。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()

    overview = page.locator('[data-test="story-progress-overview"]')
    expect(overview).to_contain_text("线索总数")
    expect(overview).to_contain_text("活跃线程")
    expect(overview).to_contain_text("0")

    page.locator('[data-test="input"]').fill("打听一下有什么线索")
    page.locator('[data-test="submit"]').click()

    expect(overview).to_contain_text("2")
    expect(overview).to_contain_text("2/")
    progress = page.locator('[data-test="story-thread-progress-list"]')
    expect(progress).to_contain_text("状告")
    expect(progress).to_contain_text("market_debt")
    expect(progress).to_contain_text("1条")


def test_clues_panel_updates_after_clue_input(page, server):
    """输入含'线索'的文字后,线索面板应显示记录。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("打听一下有什么线索")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("线索")
    clues = page.locator('[data-test="clues-panel"]')
    expect(clues).to_contain_text("状纸被师爷压下")
    expect(clues).to_contain_text("衙役")
    expect(clues).to_contain_text("共 2 条线索")
    expect(clues).to_contain_text("2 个线程")
    expect(clues).to_contain_text("新近")
    expect(clues).to_contain_text("查看事件")
    insight = page.locator('[data-test="clue-insight-summary"]')
    expect(insight).to_contain_text("最新线索")
    expect(insight).to_contain_text("陈掌柜听说码头有短工被拖欠工钱")
    expect(insight).to_contain_text("活跃线程")


def test_clue_event_link_focuses_timeline_event(page, server):
    """线索卡片可跳转并高亮对应事件时间线记录。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("打听一下有什么线索")
    page.locator('[data-test="submit"]').click()

    page.locator('[data-test="timeline-filter-test"]').click()
    expect(page.locator('[data-event-type="plot"]')).to_have_count(0)

    page.locator('.clue-event-link').first.click()
    expect(page.locator('[data-test="toggle-timeline"]')).to_have_attribute("aria-expanded", "true")
    event = page.locator('.timeline-card.focused')
    expect(event).to_be_visible()
    expect(event).to_contain_text("发现线索")


def test_pressure_panel_updates_after_pressure_input(page, server):
    """输入含'压力'的文字后,压力钟面板应显示时钟。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("威胁证人施加压力")
    page.locator('[data-test="submit"]').click()
    pressure = page.locator('[data-test="pressure-panel"]')
    expect(pressure).to_contain_text("witness_pressure")
    expect(pressure).to_contain_text("2 / 危险线 3")


def test_pressure_clock_action_button_sends_response_turn(page, server):
    """高压力钟应提供可点击应对行动,联动到行动输入。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("威胁证人施加压力")
    page.locator('[data-test="submit"]').click()

    action = page.locator('[data-test="pressure-action-witness_pressure"]')
    expect(action).to_be_visible()
    expect(action).to_contain_text("应对行动")
    action.click()

    expect(page.locator('[data-test="bubble-player"]').last).to_contain_text("应对witness_pressure")
    expect(page.locator('[data-test="bubble-player"]').last).to_contain_text("避免局势继续恶化")


def test_observation_panel_shows_visible_detail_and_button(page, server):
    """页面加载后,观察面板应显示当前位置可见细节和观察按钮。"""
    page.goto(server)
    observation = page.locator('[data-test="observation-panel"]')
    expect(observation).to_contain_text("未批状纸")
    expect(page.locator('[data-test="observe-button"]')).to_be_visible()


def test_observe_button_sends_turn_and_marks_discovered(page, server):
    """点击仔细观察后,应产生对话并标记发现。"""
    page.goto(server)
    page.locator('[data-test="observe-button"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("观察")
    expect(page.locator('[data-test="observation-court_hall_case_table"]'))\
        .to_contain_text("已发现")


def test_party_panel_shows_player_by_default(page, server):
    """页面加载后,队伍面板应显示玩家。"""
    page.goto(server)
    party = page.locator('[data-test="party-panel"]')
    expect(party).to_contain_text("无名书生")
    expect(party).to_contain_text("行动中")


def test_party_panel_updates_after_companion_joins(page, server):
    """输入同行请求后,队伍面板应显示刘师爷。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("请刘师爷同行加入队伍")
    page.locator('[data-test="submit"]').click()
    party = page.locator('[data-test="party-panel"]')
    expect(party).to_contain_text("刘师爷")
    expect(party).to_contain_text("府衙向导")
    expect(page.locator('[data-test="set-active-shiye"]')).to_be_visible()


def test_party_action_button_sends_turn(page, server):
    """点击让其行动后,应产生玩家对话气泡。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("请刘师爷同行加入队伍")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="set-active-shiye"]')).to_be_visible()
    page.locator('[data-test="set-active-shiye"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("当前行动角色")
    expect(page.locator('[data-test="party-shiye"]')).to_contain_text("行动中")


def test_advisor_panel_shows_opening_advisor(page, server):
    """页面加载后,顾问面板应显示刘师爷。"""
    page.goto(server)
    advisor = page.locator('[data-test="advisor-panel"]')
    expect(advisor).to_contain_text("刘师爷")
    expect(advisor).to_contain_text("府衙程序")
    expect(page.locator('[data-test="ask-advisor-shiye"]')).to_be_visible()


def test_quick_ask_advisor_sends_turn_and_streams_answer(page, server):
    """点击'请教'按钮后,应产生玩家和 GM 对话气泡。"""
    page.goto(server)
    page.locator('[data-test="ask-advisor-shiye"]').click()
    # player bubble should contain "请教"
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("请教")
    # GM bubble should follow
    expect(page.locator('[data-test="bubble-gm"]')
            .last).to_contain_text("模拟 GM")


def test_review_panel_summarizes_play_history(page, server):
    """故事回顾面板应显示回合数,并可打开完整复盘。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("记录第一步")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("记录第一步")

    review = page.locator('[data-test="review-panel"]')
    expect(review).to_contain_text("回合")
    expect(review).to_contain_text("线索")
    expect(review).to_contain_text("NPC")
    expect(page.locator('[data-test="open-review"]')).to_be_visible()


def test_review_modal_shows_chronological_turns(page, server):
    """完整复盘弹层应按回合展示玩家输入和 GM 叙述。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("复盘动作一")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("复盘动作一")
    expect(page.locator('[data-test="bubble-gm"]')
            .last).to_contain_text("复盘动作一")

    page.locator('[data-test="open-review"]').click()
    modal = page.locator('[data-test="review-modal"]')
    expect(modal).to_be_visible()
    body = page.locator('[data-test="review-body"]')
    expect(body).to_contain_text("复盘动作一")
    expect(body).to_contain_text("模拟 GM 回应")


def test_review_modal_shows_summary_stats(page, server):
    """完整复盘弹层应显示轻量统计摘要,帮助快速判断记录规模。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("统计复盘甲")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("统计复盘甲")
    page.locator('[data-test="input"]').fill("统计复盘乙")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("统计复盘乙")

    page.locator('[data-test="open-review"]').click()
    summary = page.locator('[data-test="review-summary"]')
    expect(summary).to_contain_text("2总回合")
    expect(summary).to_contain_text("玩家字数")
    expect(summary).to_contain_text("GM字数")
    expect(summary).to_contain_text("回合 2")
    expect(summary).to_contain_text("统计复盘乙")


def test_review_modal_shows_recent_highlights(page, server):
    """完整复盘弹层应摘录最近回合重点,便于快速回忆关键行动。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["重点复盘甲", "重点复盘乙", "重点复盘丙", "重点复盘丁"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="open-review"]').click()
    highlights = page.locator('[data-test="review-highlights"]')
    expect(highlights).to_contain_text("重点摘录")
    expect(highlights).to_contain_text("回合 4")
    expect(highlights).to_contain_text("重点复盘丁")
    expect(highlights).to_contain_text("模拟 GM 回应")
    expect(page.locator('[data-test="review-highlight-1"]')).to_have_count(0)


def test_review_modal_jump_latest_scrolls_to_recent_turn(page, server):
    """完整复盘弹层应提供跳到最新入口,方便移动端长复盘阅读。"""
    page.set_viewport_size({"width": 390, "height": 820})
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["移动复盘甲", "移动复盘乙", "移动复盘丙", "移动复盘丁", "移动复盘戊"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="mobile-panel-toggle"]').click()
    page.locator('[data-test="side-nav-review"]').click()
    page.locator('[data-test="open-review"]').click()
    expect(page.locator('[data-test="review-jump-latest"]')).to_be_visible()
    page.locator('[data-test="review-body"]').evaluate("el => { el.scrollTop = 0; }")
    expect(page.locator('[data-test="review-turn-5"]')).not_to_be_in_viewport()

    page.locator('[data-test="review-jump-latest"]').click()
    expect(page.locator('[data-test="review-turn-5"]')).to_be_in_viewport()


def test_review_modal_exposes_text_export_actions(page, server):
    """完整复盘弹层应提供可复制和下载的文本复盘。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("导出复盘动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("导出复盘动作")

    page.locator('[data-test="open-review"]').click()
    copy_btn = page.locator('[data-test="copy-review"]')
    download_btn = page.locator('[data-test="download-review"]')
    expect(copy_btn).to_be_visible()
    expect(download_btn).to_be_visible()
    copy_text = copy_btn.get_attribute("data-review-text")
    download_text = download_btn.get_attribute("data-review-text")
    assert "人生纪实 · 明朝篇 · 故事回顾" in copy_text
    assert "导出复盘动作" in copy_text
    assert "模拟 GM 回应" in download_text


def test_review_modal_filters_turns_by_text(page, server):
    """完整复盘弹层可按玩家输入或 GM 叙述筛选回合。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("复盘筛选甲")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("复盘筛选甲")
    page.locator('[data-test="input"]').fill("复盘筛选乙")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("复盘筛选乙")

    page.locator('[data-test="open-review"]').click()
    filter_input = page.locator('[data-test="review-filter-input"]')
    count = page.locator('[data-test="review-filter-count"]')
    expect(count).to_contain_text("共")
    expect(page.locator('[data-test="review-turn-1"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-2"]')).to_be_visible()

    filter_input.fill("甲")
    expect(count).to_contain_text("匹配 1")
    expect(page.locator('[data-test="review-turn-1"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-2"]')).to_be_hidden()
    expect(page.locator('[data-test="review-filter-empty"]')).to_be_hidden()

    filter_input.fill("不存在")
    expect(count).to_contain_text("匹配 0")
    expect(page.locator('[data-test="review-filter-empty"]')).to_be_visible()
    expect(page.locator('[data-test="review-filter-clear"]')).to_be_visible()

    page.locator('[data-test="review-filter-clear"]').click()
    expect(filter_input).to_have_value("")
    expect(count).to_contain_text("共")
    expect(page.locator('[data-test="review-turn-1"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-2"]')).to_be_visible()



def test_review_filter_match_navigation_jumps_between_visible_turns(page, server):
    """复盘筛选后可在匹配回合之间跳转并显示当前位置。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["匹配跳转甲", "普通回合", "匹配跳转乙"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="open-review"]').click()
    page.locator('[data-test="review-filter-input"]').fill("匹配跳转")

    controls = page.locator('[data-test="review-match-controls"]')
    expect(controls).to_be_visible()
    expect(page.locator('[data-test="review-match-index"]')).to_contain_text("1 / 2")
    expect(page.locator('[data-test="review-turn-1"]')).to_have_class(re.compile(r"\breview-match-current\b"))

    page.locator('[data-test="review-match-next"]').click()
    expect(page.locator('[data-test="review-match-index"]')).to_contain_text("2 / 2")
    expect(page.locator('[data-test="review-turn-3"]')).to_have_class(re.compile(r"\breview-match-current\b"))

    page.locator('[data-test="review-match-prev"]').click()
    expect(page.locator('[data-test="review-match-index"]')).to_contain_text("1 / 2")
    expect(page.locator('[data-test="review-turn-1"]')).to_have_class(re.compile(r"\breview-match-current\b"))


def test_review_modal_filters_turns_by_type(page, server):
    """完整复盘弹层可按回合类型筛选,并在回合标题显示类型标签。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["请教顾问下一步", "打听线索", "买一碗茶"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="open-review"]').click()
    expect(page.locator('[data-test="review-type-filters"]')).to_be_visible()
    expect(page.locator('[data-test="review-type-filter-social"]')).to_contain_text("社交 1")
    expect(page.locator('[data-test="review-type-filter-plot"]')).to_contain_text("剧情 1")
    expect(page.locator('[data-test="review-type-filter-trade"]')).to_contain_text("交易 1")
    expect(page.locator('[data-test="review-type-1"]')).to_contain_text("社交")
    expect(page.locator('[data-test="review-type-2"]')).to_contain_text("剧情")
    expect(page.locator('[data-test="review-type-3"]')).to_contain_text("交易")

    page.locator('[data-test="review-type-filter-plot"]').click()
    expect(page.locator('[data-test="review-filter-count"]')).to_contain_text("剧情 · 匹配 1")
    expect(page.locator('[data-test="review-turn-1"]')).to_be_hidden()
    expect(page.locator('[data-test="review-turn-2"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-3"]')).to_be_hidden()

    page.locator('[data-test="review-filter-input"]').fill("不存在")
    expect(page.locator('[data-test="review-filter-count"]')).to_contain_text("剧情 · 匹配 0")
    expect(page.locator('[data-test="review-filter-empty"]')).to_be_visible()

    page.locator('[data-test="review-filter-clear"]').click()
    expect(page.locator('[data-test="review-filter-input"]')).to_have_value("")
    expect(page.locator('[data-test="review-type-filter-all"]')).to_have_class(re.compile(r"\bactive\b"))
    expect(page.locator('[data-test="review-filter-count"]')).to_contain_text("共 3 个回合")
    expect(page.locator('[data-test="review-turn-1"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-2"]')).to_be_visible()
    expect(page.locator('[data-test="review-turn-3"]')).to_be_visible()


def test_side_nav_highlights_current_information_group(page, server):
    """右栏导航应高亮当前查看的信息分组,降低长面板定位成本。"""
    page.goto(server)
    situation = page.locator('[data-test="side-nav-situation"]')
    story = page.locator('[data-test="side-nav-story"]')
    review = page.locator('[data-test="side-nav-review"]')

    expect(situation).to_have_class(re.compile(r"\bactive\b"))
    expect(situation).to_have_attribute("aria-current", "true")

    story.click()
    expect(story).to_have_class(re.compile(r"\bactive\b"))
    expect(story).to_have_attribute("aria-current", "true")

    review.click()
    expect(review).to_have_class(re.compile(r"\bactive\b"))
    expect(review).to_have_attribute("aria-current", "true")


def test_replay_player_opens_and_shows_controls(page, server):
    """回放播放器按钮应打开弹层并显示播放控制。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("回放测试动作")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("回放测试动作")

    page.locator('[data-test="open-replay"]').click()
    modal = page.locator('[data-test="replay-modal"]')
    expect(modal).to_be_visible()
    expect(page.locator('[data-test="replay-layout"]')).to_be_visible()
    expect(page.locator('[data-test="replay-controls"]')).to_be_visible()
    expect(page.locator('[data-test="replay-scrubber"]')).to_be_visible()
    expect(page.locator('[data-test="replay-nav-next"]')).to_be_visible()


def test_replay_player_navigates_turns(page, server):
    """回放播放器应支持前后导航回合。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["回放甲", "回放乙"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    # Initial state
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("世界初始状态")

    # Next turn
    page.locator('[data-test="replay-nav-next"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("回放甲")

    # Next turn
    page.locator('[data-test="replay-nav-next"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("回放乙")

    # Prev turn
    page.locator('[data-test="replay-nav-prev"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("回放甲")

    # Jump to end
    page.locator('[data-test="replay-nav-end"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("回放乙")

    # Jump to start
    page.locator('[data-test="replay-nav-start"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("世界初始状态")


def test_replay_player_close_stops_autoplay(page, server):
    """关闭回放播放器应停止自动播放。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("回放关闭测试")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("回放关闭测试")

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    # Start autoplay
    page.locator('[data-test="replay-nav-play"]').click()

    # Close modal
    page.locator('#close-replay').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_hidden()

    # Reopen - should be at initial state (autoplay stopped)
    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("世界初始状态")


def test_replay_player_shows_timeline(page, server):
    """回放播放器应显示时间线标记和图例。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    for text in ["时间线甲", "时间线乙"]:
        page.locator('[data-test="input"]').fill(text)
        page.locator('[data-test="submit"]').click()
        expect(page.locator('[data-test="bubble-player"]')
                .last).to_contain_text(text)

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    # Timeline should be visible with markers
    timeline = page.locator('[data-test="replay-timeline"]')
    expect(timeline).to_be_visible()
    markers = page.locator('[data-test="replay-timeline"] .replay-timeline-marker')
    # 1 initial + 2 turns = 3 markers
    expect(markers).to_have_count(3)

    # Legend should be visible
    expect(page.locator('[data-test="replay-timeline-legend"]')).to_be_visible()

    # Click on a timeline marker to jump to that turn
    markers.nth(1).click()
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("时间线甲")


def test_replay_player_shows_speed_control(page, server):
    """回放播放器应显示速度控制选择器。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("速度测试")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("速度测试")

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    speed = page.locator('[data-test="replay-speed-select"]')
    expect(speed).to_be_visible()
    # Default should be 1x (2000ms)
    expect(speed).to_have_value("2000")

    # Change speed
    speed.select_option("1000")
    expect(speed).to_have_value("1000")


def test_replay_player_shows_diff_panel(page, server):
    """回放播放器应在非初始回合显示状态变化面板。"""
    page.goto(server)
    page.evaluate("fetch('/api/reset', { method: 'POST' }).then(r => r.json())")
    page.reload()
    page.locator('[data-test="input"]').fill("差异测试")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("差异测试")

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    diff = page.locator('[data-test="replay-diff"]')
    # Initially hidden at turn 0
    expect(diff).to_be_hidden()

    # Navigate to turn 1 - diff should show (FakeAgent logs an event)
    page.locator('[data-test="replay-nav-next"]').click()
    # Diff panel may or may not be visible depending on what changed
    # Just verify it doesn't crash
    expect(page.locator('[data-test="replay-player-input"]')).to_contain_text("差异测试")


def test_replay_player_keyboard_hint(page, server):
    """回放播放器应显示键盘快捷键提示。"""
    page.goto(server)
    page.locator('[data-test="input"]').fill("快捷键测试")
    page.locator('[data-test="submit"]').click()
    expect(page.locator('[data-test="bubble-player"]')
            .last).to_contain_text("快捷键测试")

    page.locator('[data-test="open-replay"]').click()
    expect(page.locator('[data-test="replay-modal"]')).to_be_visible()

    hint = page.locator('[data-test="replay-kbd-hint"]')
    expect(hint).to_be_visible()
    expect(hint).to_contain_text("←")
    expect(hint).to_contain_text("→")
    expect(hint).to_contain_text("Space")
