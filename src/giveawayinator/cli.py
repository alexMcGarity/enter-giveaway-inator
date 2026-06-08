"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys
import time

from rich.console import Console

from .config import load_config
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

    if args.watch:
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
