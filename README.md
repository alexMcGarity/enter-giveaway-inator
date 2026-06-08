# enter-giveawayinator

Finds Pokemon card giveaways on TikTok and tells you what you need to do to enter,
so you can enter the ones you actually want, by hand, in seconds.

It is a **discovery + notification** tool, not an auto-entry bot. It reads public
hashtag pages, classifies giveaway posts, parses the entry requirements out of the
caption (follow / like / comment / tag N friends / deadline), de-dupes against posts
you've already been shown, and pushes an alert to the console, your desktop, or Discord.

**Live giveaways are flagged specially.** When a giveaway is running on a TikTok LIVE
stream (where you join by tapping the in-stream Giveaway / treasure-box button rather
than commenting), it's marked 🔴 LIVE, sorted to the top of the batch because it's
time-sensitive, and the alert links straight to `@creator/live` so you can jump in and
tap the button. Live tiles are detected both from `/live` links on hashtag pages and
from caption signals ("giveaway on live", "treasure box", "join my live", etc.).

## Why not full auto-entry?

Three reasons, and they're the whole reason this is shaped the way it is:

1. **TikTok's ToS prohibits automation.** Bot-driven scrolling and interaction gets
   accounts shadowbanned or permanently banned, and TikTok's detection is good.
2. **Giveaways prohibit bot entries.** Automated/multiple entries are almost always
   grounds for disqualification, so an auto-entered "win" is usually void on inspection.
3. **It's an unwinnable arms race.** No public API, heavy anti-bot, constant breakage.

So this tool keeps a human in the loop: it does the tedious *finding and reading*, you
do the 10-second *entering*. That's the part that's both legal-ish and actually works.

## Install

```bash
pip install -e .
# Only if you'll use the live TikTok source:
pip install playwright && playwright install chromium
```

## Configure

```bash
cp config.example.toml config.toml
# edit hashtags, keywords, and notify channels
```

The default `source.kind = "sample"` replays a few bundled example posts so you can see
the whole thing work without touching TikTok.

## Run

```bash
# One pass over the sample data (no scraping):
giveawayinator --source sample

# One pass over live TikTok hashtag pages:
giveawayinator                       # uses source.kind from config.toml

# Keep watching, re-scan every 30 minutes:
giveawayinator --watch 30
```

## Architecture

```
sources/   how posts come in     (sample replay | TikTok via Playwright)
parser.py  is this a giveaway? live or not? what does it ask for?  (regex, unit-tested)
store.py   SQLite dedupe so you're not pinged twice
notifiers/ where alerts go       (console | desktop | discord webhook)
pipeline.py  fetch -> filter -> parse -> dedupe -> notify
cli.py     argparse front door, optional --watch loop
```

Each layer is a small interface, so swapping the parser for an LLM, adding an Instagram
source, or adding an email notifier is a single new file plus a registry line.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Responsible use

The TikTok source browses **public** pages, read-only, rate-limited, and never logs in
or interacts. It exists to surface giveaways for a human. You are responsible for staying
within TikTok's Terms and each giveaway's rules. If you hit a login wall or challenge,
stop — don't try to defeat it.

## License

MIT
