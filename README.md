# enter-giveaway-inator

A tool that discovers Pokemon card giveaways on TikTok (and Whatnot) and notifies you with
the parsed entry requirements, so you enter the ones you want by hand.

It is also a case study in engineering judgment: a project where the code was rarely the
hard part, and the most valuable output was correctly working out *when an approach would
not work, and why*.

> **Status: shelved on purpose.** It was built, tested, deployed to the cloud running 24/7,
> and then deliberately wound down once the core goal (real-time *live* giveaways) proved
> structurally unsolvable on a hobby budget. The reasoning is in [Why it's shelved](#why-its-shelved).
> The lesson turned out to be the deliverable.

## What it does

- Scans TikTok for Pokemon giveaway posts, parses the entry requirements out of each
  caption (follow / like / comment / save / tag N friends / deadline), de-dupes against
  what you have already seen, and alerts you via console, desktop, Discord, or phone push.
- Flags **live** giveaways and routes them to your phone, because live entry happens in the app.
- **Pluggable by design.** Sources, notifiers, and the parser are each small interfaces, so
  adding a platform or an alert channel is a single new file plus one registry line.
- **Runs offline out of the box.** A bundled `sample` source replays example posts so the
  whole pipeline works with zero scraping.

## The interesting part: an engineering story told in constraints

Every step below was a real wall hit in practice, diagnosed from logs and tests, then
resolved with a deliberate tradeoff.

1. **Scope / ethics.** The original ask was to *auto-enter* giveaways. I redirected to
   discovery + notify: auto-entry violates TikTok's ToS, voids giveaway entries (bots get
   disqualified), and is an unwinnable anti-bot arms race. The tool gets you one tap away;
   the tap stays human.
2. **Live discovery is login-gated.** TikTok hides live-stream discovery behind login.
   Rather than log a bot in, the tool hands you off into your own logged-in browser.
3. **The live entry button is mobile-only.** TikTok's live giveaway button exists only in
   the app, so live entry is a phone job. The `ntfy` channel pushes live giveaways to your
   phone with a tap action that deep-links into the app.
4. **The cloud cannot scrape TikTok.** A 24/7 worker on Fly.io returned zero results:
   TikTok blocks datacenter IPs with a login wall. Fix: offload scraping to an Apify actor
   that runs on its own infrastructure and returns JSON, which a datacenter IP may fetch.
5. **Containerized Chromium hung, then OOM'd.** Classic container gotchas, diagnosed from a
   silent hang and then a `TargetClosedError`: Chromium needs `--no-sandbox` and
   `--disable-dev-shm-usage`, plus 1 GB of RAM.
6. **Pay-per-result economics.** The Apify actor charges ~$0.0037 per result; the naive
   15-minute cadence projected to ~$960/mo against a $5/mo free tier. Throttled to fixed
   daytime scans with DST-aware clock-time scheduling, inside budget.
7. **Stale results.** Scans stopped notifying because hashtag mode returns the same
   all-time-popular posts every run (everything de-duped to nothing). Switched to
   search-by-newest in a 24-hour window so each scan brings genuinely fresh posts.
8. **The Whatnot pivot.** Explored Whatnot (huge for Pokemon). Same posture: API
   auth-gated, no open discovery, and giveaways are in-stream 5-minute events requiring
   presence at the draw. Added a Whatnot source in one drop-in module and learned its
   different giveaway vocabulary ("FREE booster box", "giveys") to teach the parser
   (giveaway detection on real titles went from 1/15 to 5/15).
9. **The honest conclusion.** Live giveaways are a *real-time* problem (5-minute windows). A
   polling scraper cannot beat that latency, and there is no free, frequent, no-login route
   to live data. The right tool for the live case is the platforms' own native "creator
   went live" push notifications. So the project was wound down with a clear-eyed
   conclusion rather than thrown more money or code.

## Architecture

```
fetch (Source) -> filter -> parse (giveaway? live? requirements?) -> dedupe (Store)
  -> sort live-first -> notify (Notifiers)
```

- **Sources:** `sample` (offline), `tiktok` (Playwright, residential IP), `apify` (TikTok
  via an Apify actor, search-by-latest), `whatnot` (live shows via an Apify actor). One
  `build_source()` registry.
- **Parser:** regex heuristics, fully offline and unit-tested. The one place an LLM parser
  would slot in, behind the same `parse()` function.
- **Notifiers:** console (rich), desktop (plyer), Discord webhook, ntfy phone push, browser
  handoff. All opt-in via config.
- **Store:** SQLite de-dupe (on a persistent volume in the cloud build).
- **Scheduling:** interval (`--watch`) or fixed clock times (`--at 10:00,17:00 --tz
  America/Chicago`, DST-aware via `zoneinfo`).

39 tests, all offline (injected fetchers / openers), so the suite never touches the network.

## Run it

```bash
pip install -e .
cp config.example.toml config.toml

# See the whole pipeline on bundled sample data, no scraping:
giveawayinator --source sample
```

Live sources are documented in [config.example.toml](config.example.toml): the `tiktok`
source needs Playwright (`playwright install chromium`); the `apify` and `whatnot` sources
need an `APIFY_TOKEN`. The cloud build (a containerized worker for Fly.io) lives in
[Dockerfile](Dockerfile), [fly.toml](fly.toml), and [config.cloud.toml](config.cloud.toml).

## Why it's shelved

The goal was time-sensitive *live* giveaways. The access reality:

| Route | Free? | Real-time? | Verdict |
| --- | --- | --- | --- |
| TikTok video posts | yes (residential IP) | n/a, deadline-based | works, but not the live goal |
| TikTok / Whatnot live | no (login-gated) | platforms gate it | not reachable without login |
| Apify actors | no (pay per result) | cost scales with frequency | works, too costly to poll fast |

No combination gives free + frequent + live. And even a paid real-time poller loses to the
platforms' native go-live notifications. So the tool's real niche is *deadline-based*
discovery, and the *live* niche belongs to native notifications. The project is parked with
nothing running and nothing billing; everything is reproducible from the repo.

## Tech

Python 3.11+, Playwright, Apify, Fly.io + Docker, SQLite, ntfy, Discord webhooks, `rich`,
`zoneinfo`. Pluggable source/notifier interfaces, 39 offline tests.

## License

MIT
