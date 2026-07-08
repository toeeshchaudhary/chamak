# Chamak — project notes for Claude

Project-level context so future sessions can be effective without re-deriving
everything from scratch. Treat this as instructions, not background reading.

## What this is

Chamak is an **investor reasoning engine** for Indian markets. Primary
object: a **MindMap** (called "Investing Style" in the UI) — a graph of
beliefs + rules. Recommendations are an *output* of evaluating stocks
against the graph, never a prediction of future prices.

Author: Toeesh Chaudhary. 12 A.

## Running

```bash
uv run chamak                 # launch (Simple mode default)
uv run chamak demo pilot      # interactive autopilot demo
uv run chamak demo reset -y   # wipe all data
uv run pytest -q              # 82 tests
```

The CLI entry point is `chamak.cli:app` (Typer). Console script is named
`chamak`. After `uv tool install --reinstall .`, `chamak` is on `PATH`
globally; while iterating, prefer `uv run chamak` so changes are picked up
without reinstall.

## Two modes — Simple and Advanced

- **Simple mode** is the default. 3-question quiz → big stock cards with
  star ratings, plain-English reasons, candlestick charts → Vibe Check
  mini-game → flowchart reveal.
- **Advanced mode** is the original: editor, scanner, portfolios, news,
  history, command palette, search.

Mode is stored in `~/.local/share/chamak/settings.json` via
`chamak.config.get_mode()` / `set_mode()`. `Ctrl+M` toggles at runtime.
`ChamakApp(force_mode=...)` overrides in tests.

In user-facing strings, **always say "Investing Style"** not "Mind Map".
Internal code keeps `MindMap` for clarity.

## Critical gotchas (real bugs we hit — do not repeat)

1. **`_render` shadows Textual's `Widget._render()`.** Naming a Screen
   method `_render` causes Textual to call your function expecting a
   `Visual`, get `None`, and crash with
   `AttributeError: 'NoneType' object has no attribute 'render_strips'`.
   Use suffixed names — `_refresh_card`, `_render_q`, `_render_round`,
   `_render_question`. Same lesson applies to any base-class method.

2. **`tree`, `name` (and a few others) are properties on `DOMNode`.**
   Assigning `self.tree = MindMapTree()` inside `compose()` raises
   `AttributeError: property 'tree' of '...' object has no setter`.
   Rename to `self.mm_tree`, `self.name_input`, etc. Check with
   `dir(Screen)` before adding a new instance attribute on a Screen
   subclass.

3. **`ListView.append()` only works after the ListView is mounted.**
   Inside `compose()` you must pass items via the constructor:
   `ListView(*[ListItem(...) for ...])`. Once mounted (e.g. in
   `on_mount` or later), `lv.mount(item)` or `lv.append(item)` work.

4. **`pilot.press("1")` is flaky for number/punctuation keys in the
   Textual test pilot.** When a test needs to advance quiz state etc.,
   call the action method directly (`scr._pick(0)`) rather than fighting
   the pilot. Real keyboard input works fine.

5. **`sqlite3.executescript()` issues an implicit COMMIT.** Don't wrap
   it inside the `transaction()` context manager. The migrator does
   `executescript` outside the txn, then a separate `transaction()`
   block for the `schema_version` insert.

## Architecture decisions worth remembering

- **SQLite + JSON1, not Neo4j.** Graphs are small (hundreds of nodes per
  style). NetworkX is the in-memory representation; SQLite is the
  persistence layer. Snapshots — not event sourcing — for versioning.
- **No `eval`/`exec` anywhere.** Rules compile to a closed AST
  (`cmp`/`btw`/`and`/`or`/`not`/`ref`/`lit`) evaluated by a hand-written
  interpreter (`chamak.rules.evaluator`).
- **Soft sigmoid thresholds** so a stock that just misses a rule scores
  ~0.5, not 0. Steepness `k` per metric comes from the metric registry.
- **Hard rules gate score to 0**, surfaced as deal-breakers in the
  verdict. `polarity="avoid"` inverts satisfaction at score time.
- **LLM is fully optional.** App must work with `OPENROUTER_API_KEY`
  unset. LLM is *never* allowed in scoring/ranking/threshold selection.
  It only suggests *candidates* a human approves.
- **All demo data is bundled** (`chamak/demo/data.py`,
  `chamak/demo/mindmaps.py`, `chamak/demo/news.py`,
  `chamak/demo/prices.py`). No network required for demos / tests.
  Synthetic OHLCV is seeded by ticker name → stable across runs.

## Layout reference

```
src/chamak/
  config.py          XDG paths, settings, mode preference
  cli.py             typer entry (chamak)
  core/              pydantic models, ids, errors
  storage/           SQLite + migrations + repositories
  graph/             MindMapGraph (networkx), serialize, diff
  rules/             ast, parser, metrics registry, evaluator,
                     compiler, candidates, plain (NL translator)
  interview/         YAML script, state machine, archetype, assistant
  market_data/       yfinance adapter, tickers, cache, ingest, universe
  news/              base protocols, RSS stub, sentiment classifier, repo
  scoring/           weighted-rule engine + ScoreBreakdown
  recommendation/    ranker
  portfolio/         contradiction / sector concentration analyzer
  explain/           render.py (plain + plain_english), verdict tiers
  llm/               LLMClient protocol + OpenRouter + Null
  demo/              data, mindmaps, news, prices, seeder
  tui/
    app.py           ChamakApp, mode-aware boot
    theme.py         grayscale + accent CSS
    widgets/         flowchart, candle, score_bar, banner, node_tree
    screens/         Advanced-mode screens
    simple/          Simple-mode screens (welcome, quiz, home,
                     stock_card, vibe_check, autopilot, style_builder,
                     quiz_data, explain_friendly)
```

## Conventions

- Plain English in every user-facing string. Use
  `chamak.rules.plain.translate_rule()` for AST → prose. Never show raw
  `"debt_to_equity < 0.5"` to a user.
- Verdict tiers from `chamak.explain.verdict.for_score()`:
  `STRONG FIT` ≥ 75% · `GOOD FIT` ≥ 60% · `MIXED` ≥ 45% · `POOR FIT`
  otherwise. Hard-rule failure overrides to "doesn't fit".
- Simple mode prefers **star ratings** (`★ ★ ★ ★ ★`) over percentages
  in cards. Advanced mode shows both.
- Theme keeps a grayscale base with selective accent colors
  (`#88c0d0` blue accent, `#98c379` green = good, `#e06c75` red = bad,
  `#e5c07b` amber = warning). Backgrounds: `#0a0a0d` / `#14141a`.
  Aligns with the user's i3/picom aesthetic — no animations, no
  flashy chrome.

## Testing

- `uv run pytest -q` — full suite, 82 tests in <60 s.
- `tests/test_tui_all_screens.py` mounts every screen in isolation.
  Add a test there for any new screen — that's how we catch
  shadowing-property bugs at CI time, not at user runtime.
- `tests/test_demo_recording.py` is the recording rehearsal — seeds,
  scores against each prebuilt style, asserts the top-line numbers
  match the script, drives the autopilot through every scene. Run
  before recording.
- The autouse `_isolate_xdg` fixture in `tests/conftest.py` rewires
  XDG dirs to `tmp_path`, so tests never touch the real user DB.
- For Textual screen tests, prefer `force_mode="advanced"` (or
  `simple`) on `ChamakApp(...)` so the test doesn't depend on whatever
  the user has saved in `settings.json`.

## When making changes

- Run `uv run pytest -q` before declaring anything done.
- After any change to a TUI screen, run `tests/test_tui_all_screens.py`
  and confirm the screen still mounts.
- If you add a method to a `Screen` subclass, **check it doesn't
  shadow a property on `DOMNode` / `Widget` / `Screen`**:
  ```python
  python -c "from textual.screen import Screen; print('tree' in dir(Screen))"
  ```
- Never use `eval`/`exec` for any rule-related code. Extend the AST
  instead.
- Never add LLM-driven scoring or threshold selection. LLM is for
  suggestions a human reviews.
- Keep the CLI surface stable: `chamak`, `chamak simple`,
  `chamak advanced`, `chamak demo {seed,pilot,reset,simple,advanced,
  walkthrough}`, `chamak ingest`, `chamak db migrate`,
  `chamak interview`, `chamak list-mindmaps`, `chamak tui`.

## Known quirks

- Number-key bindings (`1`/`2`/`3`) in the Textual test pilot don't
  always dispatch. Tests for the quiz call `scr._pick(0)` directly.
  Real keyboards are fine.
- yfinance occasionally returns empty fields for Indian tickers; the
  adapter degrades gracefully and the cache covers the gap. Demo mode
  never calls yfinance.
- `OPENROUTER_API_KEY` enables narrative-rule extraction; absent, the
  heuristic in `chamak.rules.candidates` covers common patterns.
