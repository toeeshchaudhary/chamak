from __future__ import annotations

import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from chamak.config import paths, setup_logging
from chamak.interview.assistant import best_available
from chamak.interview.engine import InterviewEngine
from chamak.market_data.ingest import ingest as ingest_universe
from chamak.storage.db import connect
from chamak.storage.migrator import migrate as migrate_db
from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo

app = typer.Typer(help="Chamak — investor reasoning engine.", no_args_is_help=False)
db_app = typer.Typer(help="Database management commands.")
demo_app = typer.Typer(help="Demo / autopilot commands.")
app.add_typer(db_app, name="db")
app.add_typer(demo_app, name="demo")

console = Console()


@db_app.command("migrate")
def db_migrate() -> None:
    """Apply any pending schema migrations."""
    setup_logging()
    v = migrate_db()
    console.print(f"[green]schema at version {v}[/]   db={paths().db}")


@db_app.command("path")
def db_path() -> None:
    console.print(str(paths().db))


@app.command("ingest")
def ingest_cmd(
    universe: str = typer.Option("nifty50", "--universe", "-u", help="Universe name."),
    refresh: bool = typer.Option(False, "--refresh", help="Bypass the fundamentals cache."),
) -> None:
    """Pull fundamentals for a universe of stocks into the local DB."""
    setup_logging()
    migrate_db()
    conn = connect()
    try:
        report = ingest_universe(conn, universe, refresh=refresh)
    finally:
        conn.close()
    console.print(
        f"[green]ingested[/] universe={report.universe} "
        f"fetched={report.fetched}/{report.requested} failed={len(report.failed)}"
    )
    if report.failed:
        console.print(f"[yellow]failed tickers:[/] {', '.join(report.failed[:20])}"
                      + (" …" if len(report.failed) > 20 else ""))


@app.command("interview")
def interview_cmd(
    name: str = typer.Option("My Mind Map", "--name", "-n", help="Name for the resulting mind map."),
    headless: bool = typer.Option(False, "--headless", help="Text-only interview (no TUI)."),
) -> None:
    """Run the investor interview and save a starter mind map."""
    setup_logging()
    migrate_db()
    if not headless:
        from chamak.tui.app import run_app
        run_app(start_screen="interview", interview_name=name)
        return
    _run_headless_interview(name)


def _run_headless_interview(name: str) -> None:
    engine = InterviewEngine(assistant=best_available())
    console.print("[bold]Chamak Interview[/]   (Ctrl-C to abort)\n")
    while not engine.done():
        q = engine.current()
        assert q is not None
        console.print(f"[bold cyan]Q{engine.progress()[0]+1}.[/] {q['text']}")
        kind = q["kind"]
        try:
            if kind == "choice":
                for i, opt in enumerate(q["options"], 1):
                    console.print(f"   {i}. {opt['label']}")
                pick = typer.prompt("Choice").strip()
                idx = int(pick) - 1
                value = q["options"][idx]["value"]
            elif kind == "multi":
                for i, opt in enumerate(q["options"], 1):
                    console.print(f"   {i}. {opt['label']}")
                picks = typer.prompt("Comma-separated").strip()
                value = [q["options"][int(p) - 1]["value"] for p in picks.split(",") if p.strip()]
            elif kind == "scale":
                lo, hi = q["range"]
                value = int(typer.prompt(f"Scale {lo}-{hi}").strip())
            elif kind == "number":
                value = float(typer.prompt("Number").strip())
            else:  # text
                value = typer.prompt("Answer").strip()
            engine.answer(value)
        except (ValueError, IndexError, KeyboardInterrupt):
            console.print("[red]skipped[/]")
            engine.skip()
        console.print()

    snap = engine.build_snapshot(name)
    conn = connect()
    try:
        mm_repo.insert(conn, snap.mindmap)
        version = ver_repo.save_snapshot(conn, snap, message="initial from interview")
        mm_repo.replace_graph(conn, snap.mindmap.id, snap.nodes, snap.edges, snap.rules)
        mm = snap.mindmap.model_copy(update={"current_version": version.version})
        mm_repo.update_meta(conn, mm)
    finally:
        conn.close()
    console.print(
        f"[green]saved[/] '{snap.mindmap.name}'  archetype={snap.mindmap.archetype}  "
        f"nodes={len(snap.nodes)} rules={len(snap.rules)}"
    )


@app.command("list-mindmaps")
def list_mm() -> None:
    setup_logging()
    migrate_db()
    conn = connect()
    try:
        rows = mm_repo.list_all(conn, include_archived=True)
    finally:
        conn.close()
    t = Table(title="Mind Maps")
    t.add_column("ID", style="dim", no_wrap=True)
    t.add_column("Name")
    t.add_column("Archetype")
    t.add_column("v")
    t.add_column("Archived", justify="right")
    for m in rows:
        t.add_row(m.id, m.name, m.archetype, str(m.current_version), "yes" if m.archived else "")
    console.print(t)


@demo_app.command("seed")
def demo_seed() -> None:
    """Seed Indian stocks, 3 prebuilt mind maps, demo portfolio, demo news."""
    setup_logging()
    migrate_db()
    from chamak.demo.seeder import seed as do_seed
    rep = do_seed()
    console.print(
        f"[green]seeded[/]  stocks={rep.stocks}  mindmaps={rep.mindmaps}  "
        f"portfolios={rep.portfolios}  news={rep.news}   db={paths().db}"
    )


@demo_app.command("reset")
def demo_reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """Wipe all user data (mind maps, stocks, news, portfolios). Schema kept."""
    setup_logging()
    migrate_db()
    if not yes:
        ok = typer.confirm(f"This will delete every row from {paths().db}. Continue?")
        if not ok:
            console.print("[yellow]aborted[/]")
            raise typer.Exit(code=1)
    from chamak.demo.seeder import reset as do_reset
    do_reset()
    console.print(f"[green]wiped[/] {paths().db}")


@demo_app.command("pilot")
def demo_pilot() -> None:
    """Seed demo data and launch the TUI directly into autopilot (simple mode by default)."""
    setup_logging()
    migrate_db()
    from chamak.config import get_mode
    from chamak.demo.seeder import seed as do_seed
    do_seed()
    from chamak.tui.app import run_app
    start = "simple_demo" if get_mode() == "simple" else "demo_pilot"
    run_app(start_screen=start)


@demo_app.command("simple")
def demo_simple() -> None:
    """Run the interactive Simple-mode demo (best for screen recording)."""
    setup_logging()
    migrate_db()
    from chamak.demo.seeder import seed as do_seed
    do_seed()
    from chamak.tui.app import run_app
    run_app(start_screen="simple_demo", force_mode="simple")


@demo_app.command("advanced")
def demo_advanced() -> None:
    """Run the Advanced-mode autopilot (full feature tour)."""
    setup_logging()
    migrate_db()
    from chamak.demo.seeder import seed as do_seed
    do_seed()
    from chamak.tui.app import run_app
    run_app(start_screen="demo_pilot", force_mode="advanced")


@demo_app.command("walkthrough")
def demo_walkthrough() -> None:
    """Headless walkthrough: prints a sample recommendation table + explanation."""
    setup_logging()
    migrate_db()
    from chamak.demo.seeder import seed as do_seed
    from chamak.recommendation.engine import rank_from_db
    from chamak.storage.repositories import mindmaps as mm_repo, versions as ver_repo
    from chamak.explain.render import render_plain_english

    do_seed()
    conn = connect()
    try:
        target = None
        for m in mm_repo.list_all(conn):
            if m.name == "Quality Compounder":
                target = m
                break
        if not target:
            console.print("[red]Quality Compounder mind map not found.[/]")
            raise typer.Exit(code=1)
        snap = ver_repo.load_latest(conn, target.id)
        if not snap:
            console.print("[red]No snapshot.[/]")
            raise typer.Exit(code=1)
        recs = rank_from_db(conn, snap, top_k=10)
    finally:
        conn.close()
    console.print(f"\n[bold]Top 10 vs '{target.name}'[/]\n")
    t = Table(show_header=True, header_style="bold")
    t.add_column("Ticker")
    t.add_column("Score", justify="right")
    t.add_column("Confidence", justify="right")
    for r in recs:
        t.add_row(r.ticker, f"{r.score:.0%}", f"{r.confidence:.0%}")
    console.print(t)
    console.print()
    console.print(f"[bold]Why #{1}: {recs[0].ticker}[/]\n")
    console.print(render_plain_english(recs[0].breakdown, snap=snap))


@app.command("tui")
def tui_cmd() -> None:
    """Launch the Chamak TUI (uses your saved mode — simple by default)."""
    setup_logging()
    migrate_db()
    from chamak.tui.app import run_app
    run_app()


@app.command("simple")
def simple_cmd() -> None:
    """Launch in Simple mode (and set it as your default for next time)."""
    setup_logging()
    migrate_db()
    from chamak.config import set_mode
    set_mode("simple")
    from chamak.tui.app import run_app
    run_app(force_mode="simple")


@app.command("advanced")
def advanced_cmd() -> None:
    """Launch in Advanced mode (and set it as your default for next time)."""
    setup_logging()
    migrate_db()
    from chamak.config import set_mode
    set_mode("advanced")
    from chamak.tui.app import run_app
    run_app(force_mode="advanced")


@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        setup_logging()
        migrate_db()
        from chamak.tui.app import run_app
        run_app()


def main(argv: Optional[list[str]] = None) -> None:
    app(prog_name="chamak", args=argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    main()
