"""CLI entry point for mingrpg."""
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from mingrpg.audit.logger import AuditLogger
from mingrpg.core.world import World
from mingrpg.llm.agent import GMAgent
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


# --- 模型配置 (来自 cc-haha providers.json 的"小米"项) ---
DEFAULT_BASE_URL = "https://token-plan-sgp.xiaomimimo.com/anthropic"
DEFAULT_API_KEY = "tp-srtg3w0atiqiyhe84myptmcnc4xnyg6j0ej5vn8d0eoceswx"
DEFAULT_MODEL = "mimo-v2.5-pro"


BANNER = """[bold yellow]======================================
     人 生 纪 实  ·  明 朝 篇  v0.0.1
======================================[/bold yellow]
[dim]AI 原生角色扮演 · 万历十年 · 扬州府[/dim]

输入 [cyan]/quit[/cyan] 退出, [cyan]/snapshot[/cyan] 查看世界状态, [cyan]/log[/cyan] 查看最近日志
"""


def main():
    console = Console()
    console.print(BANNER)

    # 准备数据目录
    runtime_dir = Path("runtime")
    runtime_dir.mkdir(exist_ok=True)
    db_path = runtime_dir / "world.db"
    audit_path = runtime_dir / "audit.jsonl"

    # 每次启动从 scratch 开始(MVP 阶段)
    if db_path.exists():
        db_path.unlink()

    world = World(str(db_path))
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

    audit = AuditLogger(audit_path)

    api_key = os.environ.get("MINGRPG_API_KEY", DEFAULT_API_KEY)
    base_url = os.environ.get("MINGRPG_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("MINGRPG_MODEL", DEFAULT_MODEL)

    agent = GMAgent(world=world, audit=audit, model=model,
                     api_key=api_key, base_url=base_url)

    # ---- 开场白 ----
    opening = (
        "你站在扬州府衙大堂之上,正堂高悬'明镜高悬'四个鎏金大字。\n"
        "王知府正襟危坐于公案之后,左右各立两名手执水火棍的衙役;"
        "刘师爷垂手立于一侧。\n"
        "你手中攥着那张写好的状纸,心跳如鼓——\n\n"
        "你打算如何应对?"
    )
    console.print(Panel(opening, title="[bold cyan]开场[/bold cyan]",
                        border_style="cyan"))

    # ---- 主循环 ----
    while True:
        try:
            user_input = Prompt.ask("\n[bold green]你[/bold green]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]再会。[/dim]")
            break

        if not user_input.strip():
            continue
        if user_input.strip() in ("/quit", "/exit", "/q"):
            console.print("[dim]再会。[/dim]")
            break
        if user_input.strip() == "/snapshot":
            snap = world.snapshot()
            console.print(Panel(_render_snapshot(snap),
                                  title="[yellow]世界快照[/yellow]"))
            continue
        if user_input.strip() == "/log":
            _show_recent_log(audit_path, console)
            continue

        try:
            with console.status("[cyan]GM 正在思考...[/cyan]"):
                narration = agent.process_input(user_input)
        except Exception as e:
            console.print(f"[red]GM 出错: {e}[/red]")
            continue

        console.print(Panel(narration, title="[bold magenta]GM[/bold magenta]",
                              border_style="magenta"))


def _render_snapshot(snap: dict) -> str:
    t = snap.get("time", {})
    lines = [f"时间: {t.get('year','?')} {t.get('season','')} {t.get('time_of_day','')}\n"]
    for e in snap.get("entities", []):
        statuses = ",".join(s["name"] for s in e.get("status_effects", []))
        lines.append(
            f"• {e['name']} ({e['id']}) "
            f"位置={e['location']}@{e['pos']} "
            f"hp={e['attributes'].get('hp','?')} "
            f"状态=[{statuses or '无'}]"
        )
    flags = snap.get("flags", {})
    if flags:
        lines.append(f"\n剧情标记: {flags}")
    return "\n".join(lines)


def _show_recent_log(path: Path, console: Console, n: int = 1):
    if not path.exists():
        console.print("[dim]日志为空。[/dim]")
        return
    import json
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    for line in lines[-n:]:
        rec = json.loads(line)
        console.print(f"[yellow]Turn {rec['turn']}[/yellow] "
                       f"输入: {rec['player_input']}")
        for step in rec["agent_trace"]:
            if step["type"] == "tool_use":
                console.print(
                    f"  [cyan]→ {step['name']}[/cyan]"
                    f" args={step['input']}"
                )
        if rec["cited_laws"]:
            console.print(f"  [magenta]引法条:[/magenta] "
                           f"{rec['cited_laws']}")
        console.print(f"  [green]叙述:[/green] {rec['narration'][:200]}...")


if __name__ == "__main__":
    main()
