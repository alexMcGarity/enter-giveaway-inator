# enter-giveawayinator

Finds Pokemon card giveaways on TikTok and tells you exactly what you need to do to
enter, so you can enter the ones you actually want, by hand, in seconds.

It is a **discovery + notification** tool, not an auto-entry bot. It reads public
hashtag pages, classifies giveaway posts, parses the entry requirements out of the
caption (follow / like / comment / save / tag N friends / deadline), de-dupes against
posts you have already been shown, and pushes an alert to the console, your desktop, or
Discord.

> The GitHub repo is named `enter-giveaway-inator` (a Doofenshmirtz "-inator" nod). The
> local folder and the installable Python package are `enter-giveawayinator`.

## Highlights

- **Live giveaways flagged 🔴 and surfaced first.** Giveaways that look like they run on
  a TikTok LIVE stream (where you join by tapping the in-stream Giveaway / treasure-box
  button instead of commenting) are marked LIVE, sorted to the top of the batch because
  they are time-sensitive, and the alert links straight to `@creator/live`. These are
  detected from caption signals ("giveaway on live", "treasure box", "join my live") and
  any `/live` links seen while scraping.
- **Live handoff to where you can actually enter.** TikTok gates live discovery behind
  login (the bot never logs in), and the live giveaway / treasure-box entry button only
  exists in the *mobile app*, not on desktop web. So live entry is a phone job. The `ntfy`
  channel pushes live giveaways to your phone with a tap action that opens `@creator/live`
  in the TikTok app, where the button lives. For scouting on desktop,
  `giveawayinator --open-live-search` opens TikTok's LIVE search in your logged-in browser.
  The bot never authenticates and never taps the button; you do.
- **Requirement parsing.** Each alert includes a plain checklist (follow, like, comment,
  save, tag N friends) plus any deadline it can find ("ends 6/15", "winner announced Friday").
- **Won't ping you twice.** A SQLite store remembers everything it has already shown you.
- **Pluggable everywhere.** Sources, notifiers, and the parser are each small interfaces,
  so adding an Instagram source, an email notifier, or an LLM-based parser is one new file
  plus a registry line.
- **Runs offline for demos.** The bundled `sample` source replays example posts so you
  can see the whole pipeline work without touching TikTok.

## Why not full auto-entry?

You asked for auto-entry first; here is why this is shaped as discovery instead.

1. **TikTok's ToS prohibits automation.** Bot-driven scrolling and interaction gets
   accounts shadowbanned or permanently banned, and TikTok's detection is good.
2. **Giveaways prohibit bot entries.** Automated or multiple entries are almost always
   grounds for disqualification, so an auto-entered "win" is usually void on inspection.
3. **It is an unwinnable arms race.** No public API, heavy anti-bot, constant breakage.

So the tool keeps a human in the loop: it does the tedious *finding and reading*, you do
the 10-second *entering*. That is the part that is both defensible and actually works.

## Requirements

- Python 3.11 or newer (developed and tested on 3.14)
- For the live TikTok source only: Playwright plus a Chromium download

## Install

```bash
pip install -e .
# Only if you will use the live TikTok source:
pip install playwright && playwright install chromium
# Optional desktop notifications:
pip install -e ".[desktop]"
```

## Configure

```bash
cp config.example.toml config.toml
# edit hashtags, keywords, source kind, and notify channels
```

`config.toml` is gitignored (it can hold your Discord webhook), so it never ships.

### Configuration reference

| Section / key | Meaning | Default |
| --- | --- | --- |
| `search.hashtags` | Hashtags to scan on TikTok | (see example) |
| `search.keywords` | Pokemon keywords a post must mention | (see example) |
| `search.max_posts_per_hashtag` | Cap per hashtag per run | `30` |
| `source.kind` | `"sample"` (offline replay) or `"tiktok"` (Playwright) | `"sample"` |
| `source.headless` | Run the browser headless; set `false` to watch it | `true` |
| `source.min_delay` / `source.max_delay` | Polite random delay between actions (seconds) | `2.0` / `5.0` |
| `store.path` | SQLite file for the de-dupe store | `"seen.db"` |
| `notify.channels` | Any of `"console"`, `"desktop"`, `"discord"` | `["console"]` |
| `notify.discord.webhook_url` | Required if `"discord"` is enabled | `""` |
| `filter.max_age_days` | Skip posts older than this; `0` disables | `7` |
| `filter.require_pokemon_keyword` | Require a Pokemon keyword match | `true` |

## Run

```bash
# One pass over the sample data (no scraping):
giveawayinator --source sample

# One pass over live TikTok hashtag pages (uses source.kind from config.toml):
giveawayinator

# Keep watching, re-scan every 30 minutes:
giveawayinator --watch 30

# Jump into live giveaways: open TikTok LIVE search in your logged-in browser:
giveawayinator --open-live-search

# Use a different config file:
giveawayinator -c other-config.toml
```

At the end of each run it prints a summary line:
`fetched N · giveaways N · notified N · already-seen N · filtered N`.

## Notification channels

- **console** (default): a formatted panel via `rich`. Live giveaways get a red panel
  with the "tap the in-stream giveaway button" call to action.
- **desktop**: native OS toast via `plyer`. Install with `pip install -e ".[desktop]"`.
- **discord**: posts an embed to a channel webhook. Create a webhook in your Discord
  server (Channel Settings → Integrations → Webhooks), paste the URL into
  `notify.discord.webhook_url`, and add `"discord"` to `notify.channels`.
- **browser**: for live-candidate giveaways only, opens `@creator/live` in your default
  (logged-in) browser, capped per run so a busy scan does not flood you with tabs.
- **ntfy**: phone push via [ntfy.sh](https://ntfy.sh). Install the ntfy app, subscribe to
  your `notify.ntfy.topic`, and live giveaways push to your phone with a tap action that
  opens `@creator/live` in the TikTok app. This matters because the live giveaway /
  treasure-box entry button only exists in the mobile app, not on desktop web, so the
  actual entry happens on your phone. Defaults to live-only so it does not spam you.

## How it works

```
fetch  ->  filter  ->  parse  ->  dedupe  ->  sort live-first  ->  notify
```

1. **Source** yields candidate `Post`s for the configured hashtags.
2. **Filter** drops non-Pokemon posts and anything past `max_age_days`.
3. **Parser** decides if a post is a giveaway, extracts the requirement checklist and any
   deadline, and flags live giveaways.
4. **Store** skips anything already shown. Live posts are keyed per creator per day, since
   livestream giveaways recur and you want to hear about a new session.
5. **Pipeline** sorts live giveaways to the front, then dispatches each to every notifier
   and records it as seen.

## Project layout

```
src/giveawayinator/
  models.py          Post, Requirements, Giveaway dataclasses
  config.py          loads + validates config.toml
  parser.py          giveaway / live / requirement detection (regex heuristics)
  store.py           SQLite de-dupe store
  pipeline.py        glue: fetch -> filter -> parse -> dedupe -> notify
  cli.py             argparse front door, optional --watch loop
  sources/
    base.py          Source protocol
    sample.py        offline example posts
    tiktok.py        Playwright-backed public hashtag + live scraper (residential IP)
    apify.py         Apify-actor scraper returning JSON (works from the cloud)
    __init__.py      build_source() registry
  notifiers/
    base.py          Notifier protocol
    console.py       rich panels
    desktop.py       plyer toast (optional dep)
    discord.py       webhook embed
    __init__.py      build_notifiers() registry
tests/
  test_parser.py     requirement + live detection
  test_pipeline.py   end-to-end run, dedupe, live-first ordering
```

## Tests

```bash
pip install -e ".[dev]"
pytest
```

## Run in the cloud (Fly.io)

For 24/7 operation there is a containerized worker. Key facts:

- **TikTok blocks datacenter IPs.** The Playwright `tiktok` source gets a login wall from a
  cloud IP, so the cloud worker uses the **`apify`** source instead: an
  [Apify](https://apify.com) actor scrapes TikTok on its own infrastructure and returns
  JSON, which the worker fetches and runs through the same parse -> notify pipeline.
- **Headless-only channels.** The cloud config uses `console` (logs) + `discord` + `ntfy`.
  `desktop`, `browser`, and `--open-live-search` are local-only (they need your screen /
  logged-in browser), so the live entry path stays: cloud detects -> phone push -> you tap.
- **Secrets via env / Fly secrets**, never in the image: `APIFY_TOKEN`, `DISCORD_WEBHOOK_URL`,
  `NTFY_TOPIC`. `seen.db` lives on a Fly volume so dedupe survives restarts.

```bash
fly apps create enter-giveaway-inator
fly volumes create giveawayinator_data --region ord --size 1
fly secrets set APIFY_TOKEN=... DISCORD_WEBHOOK_URL=... NTFY_TOPIC=...
fly deploy --remote-only
```

See [Dockerfile](Dockerfile), [fly.toml](fly.toml), and [config.cloud.toml](config.cloud.toml).

## Maintenance notes

TikTok ships no public API and changes its page markup often, so the CSS selectors in
[`sources/tiktok.py`](src/giveawayinator/sources/tiktok.py) are best-effort and will need
occasional updates. When the live or video grid stops returning results, set
`source.headless = false` and watch what the page actually renders, then adjust the
selectors. The source bails out early if it sees a login wall instead of content.

## Responsible use

The TikTok source browses **public** pages, read-only, rate-limited, and never logs in or
interacts. It exists to surface giveaways for a human to act on. You are responsible for
staying within TikTok's Terms and each giveaway's rules. If you hit a login wall or a
challenge, stop. Do not try to defeat it.

## Roadmap ideas

- Instagram / YouTube giveaway sources behind the same `Source` interface
- Optional LLM parser for messier captions
- A small web or TUI feed instead of one-shot console output

## License

MIT
