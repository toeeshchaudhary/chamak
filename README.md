# Chamak

> An investor reasoning engine for Indian markets — it learns *your* way of picking stocks and evaluates every company through that lens.

Chamak is **not** a stock screener, a trading bot, or a price-prediction model. It captures how *you* decide what makes a good investment — your beliefs, your rules of thumb, what you avoid — turns that into a structured flowchart (an *investing style*), and then continuously checks every stock against it. When it recommends a stock, it's not because it thinks the price will go up; it's because the stock matches what *you* said you care about — and every match is explained in plain English, rule by rule.

## The idea

Most investing apps ask "what stock do you want?" and try to predict the future. That fails twice over — nobody reliably predicts short-term prices, and following someone else's "buy this" teaches you nothing. Chamak asks a different question: **"How do you decide what makes a good investment?"** It captures the answer as a graph of beliefs and rules, then continuously checks every stock against it. The reasoning stays visible (every score has an explanation you can argue with), it teaches as it works, and it stays yours — you can edit any belief at any time.

An investing style is a root goal at the top, beliefs branching beneath, and plain-English rules under each belief — e.g. a "Value Investor" style whose beliefs are *Low Debt* (owes less than 0.5× its net worth), *Margin of Safety* (priced under 20× earnings and 3× book value), and *Earn on Capital* (at least 12% on equity and capital).

## Simple and Advanced modes

Chamak ships with two modes for two kinds of users. Switch anytime with `Ctrl+M`, or pass `chamak simple` / `chamak advanced` to set the default.

| Mode | For | Highlights |
|---|---|---|
| **Simple** (default) | Anyone — no finance background; a curious 12-year-old should manage | Plain-English everywhere; a three-question quiz to find your style; stock cards with star ratings, headlines, and ASCII candlestick charts; verdict labels (`STRONG FIT` / `GOOD FIT` / `MIXED` / `POOR FIT`); the *Vibe Check* mini-game |
| **Advanced** | Full control and technical reviewers | Full mind-map editor with version history and diffs; recommendation center with rule-level breakdowns; market scanner over any universe; portfolio intelligence (contradiction detection); news intelligence with sentiment tagging; command palette (`:`), search (`/`), vim-style navigation |

## Install

Chamak runs on Python 3.12. The only thing you install is **uv** (a fast Python package manager) — it handles every other dependency, including Python itself. Install uv, then from inside the Chamak folder run `uv tool install --python 3.12 .`.

| OS | Install uv |
|---|---|
| Windows (PowerShell) | `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| macOS | `curl -LsSf https://astral.sh/uv/install.sh \| sh` — or `brew install uv` |
| Linux | `curl -LsSf https://astral.sh/uv/install.sh \| sh` — or your distro's package manager (`pacman -S uv`, `pipx install uv`, …) |

Then, from inside the unzipped Chamak folder:

```bash
uv tool install --python 3.12 .
chamak demo pilot
```

That seeds 30 Indian stocks, three pre-built investing styles, a sample portfolio, and walks you through an interactive demo. After install you should see `Installed 1 executable: chamak`, and `chamak` works from anywhere. If the shell says "command not found", reopen the terminal so `PATH` refreshes.

On Windows, use **Windows Terminal** (not classic `cmd.exe`) with a Nerd Font, Cascadia Code, or Consolas — it renders the Unicode box-drawing and candlestick characters correctly. On macOS/Linux, any Unicode-capable terminal works (Terminal.app, iTerm2, Ghostty, Alacritty, kitty).

## Run it

```bash
chamak                  # launch the app (Simple mode by default)
chamak demo pilot       # interactive guided tour (great for first-timers)
chamak demo reset -y    # wipe all data and start over
chamak simple           # force Simple mode and save as the default
chamak advanced         # force Advanced mode and save as the default
chamak --help           # full command list
```

For a clean-slate demo to record or show someone: `chamak demo reset -y && chamak demo pilot`.

Inside the app:

| Key | What it does |
|---|---|
| `?` | Help screen with every shortcut |
| `Esc` | Go back |
| `Ctrl+M` | Switch between Simple and Advanced mode |
| `Ctrl+Q` | Quit |
| `1` / `2` / `3` | Pick options in the quiz |
| `←` / `→` | Previous / next stock card |
| `space` | Next card |
| `j` / `k` | Move down / up in lists |

Advanced mode adds `L` (library), `R` (recommendations), `S` (scanner), `P` (portfolios), `N` (news), `I` (interview), `:` (command palette), and `/` (search).

## Architecture

The primary object is a **MindMap** (called "Investing Style" in the UI) — a graph of **nodes** (goals, beliefs, metrics, sectors), typed **edges** (`supports`, `contradicts`, `requires`, `strengthens`, `weakens`, `depends_on`), and machine-evaluable **rules** bound to belief nodes. Each save is an immutable snapshot in `mindmap_versions.graph_json`; diffs are computed on demand, and restore = save the older snapshot as the new latest.

- **Rules** are a small DSL (`debt_to_equity < 0.5 AND roe > 15`) parsed by a hand-written tokenizer + recursive-descent parser into a typed, closed AST (`Comparison · Between · And · Or · Not · MetricRef · Literal`). There is **no `eval`/`exec` anywhere**. The evaluator is a hand-written interpreter using **soft sigmoid thresholds**, so a stock that just misses a rule scores ~0.5 rather than a hard zero.
- **Scoring** is `score = Σ_r (w_r · sat_r · conf_r) / Σ_r (w_r · conf_r)`, where `sat_r ∈ [0,1]` is soft satisfaction, `w_r` the weight, and `conf_r` the confidence. Hard rules (deal-breakers) gate the whole score to 0 if they fail; polarity-inverted rules ("avoid expensive stocks") flip satisfaction at score time.
- **Storage** is SQLite with the JSON1 extension — one file in the user's data directory (`~/.local/share/chamak/chamak.db` on Linux, `%APPDATA%\chamak\chamak.db` on Windows, `~/Library/Application Support/chamak/chamak.db` on macOS), WAL mode enabled. No external services, no accounts, no cloud.
- **TUI rendering** is built on Textual. The flowchart and candlestick chart are hand-written ASCII renderers emitting Rich-markup strings with no external dependencies.
- **LLM (optional)** — Chamak works fully offline. Set `OPENROUTER_API_KEY` and it can extract candidate rules from a narrative and suggest interview questions. LLMs are **never** used for scoring, ranking, or price prediction.

```
src/chamak/
├── config.py                paths, settings, mode preference
├── cli.py                   `chamak` command (typer)
├── core/                    domain models + ids + errors
├── storage/                 SQLite + migrations + repositories
├── graph/                   MindMapGraph (networkx) + diff
├── rules/                   AST, parser, metric registry, evaluator, plain-English translator
├── interview/               YAML script + state machine + archetype
├── market_data/             yfinance adapter, ticker map, cache
├── news/                    sentiment classifier + storage
├── scoring/                 weighted-rule compatibility scoring
├── recommendation/          ranker
├── portfolio/               drift / contradiction detector
├── explain/                 plain renderer + verdict tiers
├── llm/                     LLMClient protocol + OpenRouter + Null
├── demo/                    seed data + prebuilt styles + price gen
└── tui/                     Textual app, theme, widgets, screens/, simple/
```

## Tech stack

| Layer | What we used | Why |
|---|---|---|
| Language | Python 3.12 | rich ecosystem, fast iteration |
| Package mgmt | [uv](https://github.com/astral-sh/uv) | fast, cross-platform installer |
| TUI framework | [Textual](https://textual.textualize.io/) | full async TUI w/ CSS-like styles |
| Data models | pydantic v2 | validated, typed domain objects |
| Graph engine | networkx | DiGraph for in-memory mind maps |
| Storage | SQLite + JSON1 | one-file local DB, no setup |
| CLI | Typer | nice argparse layer with help |
| Market data | yfinance | free Indian-market price data |
| HTTP | httpx | LLM API calls |
| YAML | PyYAML | interview script format |
| Terminal | Rich | markup + color rendering |
| Testing | pytest + pytest-asyncio | 82 tests, including TUI smoke |
| Linting | ruff | one tool, fast |

Hand-written in-house: the ASCII flowchart and candlestick renderers, the rule AST + parser + soft-threshold evaluator, the plain-English rule translator, the verdict tier system, and the explainability engine.

## Testing

```bash
uv run pytest -q
```

82 tests covering the rule compiler (missing metrics, hard-rule gating, polarity inversion), scoring formulas, graph diffing, schema migrations, the interview state machine, every TUI screen (mounts without errors), the autopilot walkthrough, the candlestick and flowchart renderers, the plain-English translator, the verdict tiers, and the demo seeder.

```bash
uv run pytest tests/test_demo_recording.py -v
```

Run that before any screen recording — it seeds the data, scores against every prebuilt style, asserts the top results match the script, and boots the autopilot through every scene.

## Credits

- **Toeesh Chaudhary** (12th A) — design, architecture, implementation.

Chamak is built for learning, not live trading — numbers in demo mode are illustrative only.

---

Built by [toeesh](https://github.com/toeeshchaudhary) · MIT licensed
