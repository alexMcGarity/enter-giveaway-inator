"""Pretty console output via rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from ..models import Giveaway

_console = Console()


class ConsoleNotifier:
    def notify(self, giveaway: Giveaway) -> None:
        post = giveaway.post
        checklist = "\n".join(f"  • {item}" for item in giveaway.requirements.as_checklist())
        deadline = giveaway.requirements.deadline

        body = f"[bold]@{post.author}[/bold]\n{post.caption}\n\n"

        if giveaway.live:
            # Live giveaways are joined by tapping the in-stream button, not by
            # commenting, so lead with that and send them straight to the stream.
            body += f"[bold red]🔴 LIVE NOW — {giveaway.post.live_entry_hint}[/bold red]\n"
            if giveaway.requirements.as_checklist()[0] != "No explicit requirements found — read the caption":
                body += f"\n[bold yellow]Also asks you to:[/bold yellow]\n{checklist}\n"
            link = post.live_url
            title = "🔴 LIVE Pokemon giveaway"
            border = "red"
        else:
            body += f"[bold yellow]To enter:[/bold yellow]\n{checklist}\n"
            link = post.url
            title = "🎁 Pokemon giveaway found"
            border = "green"

        if deadline:
            body += f"\n[bold red]Deadline:[/bold red] {deadline}\n"
        body += f"\n[link={link}]{link}[/link]"

        if giveaway.matched_keywords:
            title += f"  ({', '.join(giveaway.matched_keywords)})"
        _console.print(Panel(body, title=title, border_style=border, expand=False))
