"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from rich.console import Console

from .config import load_config
from .schedule import next_run_at, parse_times
from .notifiers import build_notifiers
from .pipeline import run_once
from .sources import build_source
from .store import SeenStore

_console = Console()


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="giveawayinator",
        description="Discover Pokemon card giveaways on TikTok and get notified.",
    )
    p.add_argument("-c", "--config", default="config.toml", help="Path to config.toml")
    p.add_argument(
        "--source",
        choices=["sample", "tiktok"],
        help="Override source.kind from config (handy for a quick sample demo).",
    )
    p.add_argument(
        "--watch",
        type=float,
        metavar="MINUTES",
        help="Re-run every MINUTES minutes instead of running once.",
    )
    p.add_argument(
        "--at",
        metavar="HH:MM,...",
        help="Run at fixed clock times each day, e.g. '10:00,17:00'. Uses --tz.",
    )
    p.add_argument(
        "--tz",
        default="America/Chicago",
        metavar="ZONE",
        help="IANA timezone for --at (default America/Chicago, i.e. US Central, DST-aware).",
    )
    p.add_argument(
        "--open-live-search",
        action="store_true",
        help="Open TikTok LIVE search for your live_queries in your browser, then exit. "
        "You are logged in there, so you see who is actually streaming and can tap in.",
    )
    return p


def _run(config, *, source_override: str | None):
    if source_override:
        config.source.kind = source_override
    source = build_source(config.source)
    notifiers = build_notifiers(config.notify)
    with SeenStore(config.store_path) as store:
        stats = run_once(config, source, store, notifiers)
    _console.print(
        f"[dim]fetched {stats.fetched} · giveaways {stats.giveaways} · "
        f"notified {stats.notified} · already-seen {stats.skipped_seen} · "
        f"filtered {stats.skipped_filtered}[/dim]"
    )


def main(argv: list[str] | None = None) -> int:
    # Windows consoles/pipes often default to cp1252, which can't render the emoji
    # in our output. Force UTF-8 so the alerts don't crash on a UnicodeEncodeError.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    args = _build_arg_parser().parse_args(argv)
    try:
        config = load_config(args.config)
    except FileNotFoundError as exc:
        _console.print(f"[red]{exc}[/red]")
        return 1

    if args.open_live_search:
        from .browser import open_live_search

        queries = config.search.live_queries
        if not queries:
            _console.print("[red]No live_queries set in config.toml.[/red]")
            return 1
        opened = open_live_search(queries)
        _console.print(
            f"[green]Opened {len(opened)} TikTok LIVE search tab(s) in your browser:[/green]"
        )
        for url in opened:
            _console.print(f"  [link={url}]{url}[/link]")
        return 0

    if args.at:
        try:
            times = parse_times(args.at)
            tz = ZoneInfo(args.tz)
        except (ValueError, KeyError) as exc:
            _console.print(f"[red]Bad --at/--tz: {exc}[/red]")
            return 1
        _console.print(
            f"[green]Scheduled scans at {args.at} {args.tz} each day. Ctrl-C to stop.[/green]"
        )
        try:
            while True:
                now = datetime.now(tz)
                nxt = next_run_at(times, now)
                sleep_s = (nxt - now).total_seconds()
                _console.print(
                    f"[dim]Next scan {nxt:%Y-%m-%d %H:%M %Z} (in {sleep_s / 3600:.1f}h)[/dim]"
                )
                time.sleep(sleep_s)
                _run(config, source_override=args.source)
        except KeyboardInterrupt:
            _console.print("\n[dim]Stopped.[/dim]")
            return 0
    elif args.watch:
        _console.print(f"[green]Watching every {args.watch} min. Ctrl-C to stop.[/green]")
        try:
            while True:
                _run(config, source_override=args.source)
                time.sleep(args.watch * 60)
        except KeyboardInterrupt:
            _console.print("\n[dim]Stopped.[/dim]")
            return 0
    else:
        _run(config, source_override=args.source)
    return 0


if __name__ == "__main__":
    sys.exit(main())
