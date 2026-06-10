# Chamak

**An investor reasoning engine for Indian markets.**

```
    ▄████▄   ██░ ██  ▄▄▄       ███▄ ▄███▓ ▄▄▄       ██ ▄█▀
   ▒██▀ ▀█  ▓██░ ██▒▒████▄    ▓██▒▀█▀ ██▒▒████▄     ██▄█▒
   ▒▓█    ▄ ▒██▀▀██░▒██  ▀█▄  ▓██    ▓██░▒██  ▀█▄  ▓███▄░
   ▒▓▓▄ ▄██▒░▓█ ░██ ░██▄▄▄▄██ ▒██    ▒██ ░██▄▄▄▄██ ▓██ █▄
   ▒ ▓███▀ ░░▓█▒░██▓ ▓█   ▓██▒▒██▒   ░██▒ ▓█   ▓██▒▒██▒ █▄
```

Made by **Toeesh Chaudhary**, with help from **Harsh Sharma** — 12th A.

---

## Table of contents

1. [What Chamak is (and isn't)](#what-chamak-is-and-isnt)
2. [The idea](#the-idea)
3. [Two modes — Simple and Advanced](#two-modes--simple-and-advanced)
4. [Quick start (60 seconds)](#quick-start-60-seconds)
5. [Installation — Windows, macOS, Linux](#installation--windows-macos-linux)
6. [Running Chamak](#running-chamak)
7. [The five-minute tour](#the-five-minute-tour)
8. [Technical architecture](#technical-architecture)
9. [Tech stack](#tech-stack)
10. [Project layout](#project-layout)
11. [Testing](#testing)
12. [Credits](#credits)

---

## What Chamak is (and isn't)

Chamak is **not** a stock screener, a trading bot, or a price-prediction model.

Chamak is an **investor reasoning engine**. It learns how *you* decide what
makes a good investment — your beliefs, your rules of thumb, what you avoid,
what you care about — turns that thinking into a structured flowchart, and
then evaluates every stock through *your* lens.

The recommendations Chamak makes are explainable. You can drill into any
suggestion and see, rule by rule, exactly why a stock matches (or doesn't
match) your way of thinking.

```
                          ╭────────────────────╮
                          │   Value Investor   │
                          ╰─────────┬──────────╯
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
  ╭─────┴──────╮             ╭──────┴──────╮             ╭──────┴──────╮
  │  Low Debt  │             │   Margin    │             │  Earn on    │
  │            │             │  of Safety  │             │   Capital   │
  ╰────────────╯             ╰─────────────╯             ╰─────────────╯
  • Owes less                • Priced under              • Earns at
    than 0.5× its              20× earnings                least 12%
    net worth                • Priced under                on equity
                               3× book value             • Earns at
                                                           least 12%
                                                           on capital
```

That's a real "investing style" inside Chamak — root goal at the top, beliefs
branching beneath, rules in plain English under each belief.

---

## The idea

Most investing apps ask you "what stock do you want?" and try to predict the
future. That has two problems:

1. Nobody — really, nobody — can reliably predict short-term stock prices.
2. Following someone else's "buy this" advice teaches you nothing about how
   to think for yourself.

Chamak asks a different question: **"How do you decide what makes a good
investment?"** It captures the answer as a graph of beliefs and rules — your
*investing style* — and then continuously checks every stock against it.

When Chamak recommends a stock, it's not because Chamak thinks the stock will
go up. It's because the stock matches what *you* said you care about. That
match (or mismatch) is shown in plain English, rule by rule.

The result is a tool that:
- **Makes its reasoning visible.** Every score has an explanation you can
  argue with.
- **Teaches as it works.** Reading why a stock matched (or didn't) is itself
  an investing lesson.
- **Stays yours.** You can edit any belief at any time. The flowchart is
  yours to refine.

---

## Two modes — Simple and Advanced

Chamak ships with two modes for two different kinds of users.

### Simple mode (the default)

For anyone — no finance background needed. Even a curious 12-year-old should
be able to use it.

- **Plain-English everywhere.** No jargon. "The company owes less than half
  its net worth" instead of "debt_to_equity < 0.5".
- **Three friendly questions** to figure out your style. Pick a card.
- **Stock cards** with star ratings, headlines, and an ASCII candlestick
  chart for each stock.
- **Verdict labels**: `STRONG FIT`, `GOOD FIT`, `MIXED`, `POOR FIT`.
- **Vibe Check** mini-game: we show you two stocks side-by-side and ask
  which you'd rather own. We tell you which one your saved style would have
  picked. It's a fun way to test whether your gut and your stated style
  agree.

### Advanced mode

For people who want full control — and for technical reviewers.

- **Full mind-map editor** with version history and diffs.
- **Recommendation center** with rule-level breakdowns.
- **Market scanner** to run your style against any universe.
- **Portfolio intelligence** — detects contradictions ("you said you avoid
  debt but you own these levered names").
- **News intelligence** with multi-label sentiment tagging.
- **Command palette** (`:`), global search (`/`), vim-style navigation.

You can switch modes anytime with `Ctrl+M` inside the app, or pass
`chamak simple` / `chamak advanced` on the command line.

---

## Quick start (60 seconds)

If you already have Python 3.12 and the `uv` package manager installed:

```bash
uv tool install chamak --from .
chamak demo pilot
```

That seeds 30 Indian stocks, three pre-built investing styles, a sample
portfolio, and walks you through an interactive demo of the whole app.

If you don't have `uv` yet, see the install section below — it's one line
on every operating system.

---

## Installation — Windows, macOS, Linux

Chamak runs on Python 3.12. The only thing you actually have to install on
your machine is **uv** (a fast Python package manager). uv handles every
other dependency, including Python itself.

### Windows

Open **PowerShell** and run:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then unzip the Chamak folder and, from inside it:

```powershell
uv tool install --python 3.12 .
chamak demo pilot
```

> **Tip:** Use **Windows Terminal** (built into Windows 11, free download on
> Windows 10) rather than the classic `cmd.exe`. Windows Terminal renders the
> Unicode box-drawing and candlestick characters correctly. Make sure the
> font is set to a Nerd Font or Cascadia Code / Consolas for the best look.

### macOS

Open **Terminal** and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or, if you use Homebrew:

```bash
brew install uv
```

Then unzip the Chamak folder and, from inside it:

```bash
uv tool install --python 3.12 .
chamak demo pilot
```

> Works in Terminal.app, iTerm2, Ghostty, Alacritty, kitty — anything with
> Unicode support.

### Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or use your distro's package manager (e.g. `pacman -S uv` on Arch,
`apt install pipx && pipx install uv` on recent Ubuntu, etc.).

Then unzip the Chamak folder and, from inside it:

```bash
uv tool install --python 3.12 .
chamak demo pilot
```

### Verifying the install

After `uv tool install` completes, you should see:

```
Installed 1 executable: chamak
```

Now `chamak` works from anywhere in the terminal:

```bash
chamak --help
```

If the shell still says "command not found", close and reopen the terminal
window (so the `PATH` refreshes) and try again.

---

## Running Chamak

Once installed, these are the commands you'll actually use:

```bash
chamak                  # launch the app (Simple mode by default)
chamak demo pilot       # interactive guided tour (great for first-timers)
chamak demo reset -y    # wipe all data and start over
chamak simple           # force Simple mode and save as the default
chamak advanced         # force Advanced mode and save as the default
chamak --help           # full command list
```

For a screen recording or a demo to show someone:

```bash
chamak demo reset -y && chamak demo pilot
```

That gives you a clean slate and immediately starts the autopilot walkthrough.

### Inside the app

| Key            | What it does                                  |
|----------------|-----------------------------------------------|
| `?`            | Help screen with every shortcut               |
| `Esc`          | Go back                                       |
| `Ctrl+M`       | Switch between Simple and Advanced mode       |
| `Ctrl+Q`       | Quit                                          |
| `1` / `2` / `3`| Pick options in the quiz                      |
| `←` / `→`      | Previous / next stock card                    |
| `space`        | Next card                                     |
| `j` / `k`      | Move down / up in lists                       |

In Advanced mode you also get `L` (library), `R` (recommendations),
`S` (scanner), `P` (portfolios), `N` (news), `I` (interview), `:` (command
palette), and `/` (search).

---

## The five-minute tour

Run `chamak demo pilot` and watch the autopilot, or:

1. **Welcome → Quiz.** Three picture-card questions in plain English.
   "Careful, balanced, or bold?" "A steady business, a fast-growing one, or
   one that pays you?" "Do you look for deals, fair prices, or pay up for
   quality?"
2. **Home.** Big friendly menu with five options.
3. **Stocks I'd like.** One card per stock, ranked. Each card shows a star
   rating, a verdict (`STRONG FIT` / `GOOD FIT` / `MIXED` / `POOR FIT`), a
   30-day candlestick chart, two or three reasons in plain English ("The
   company earns at least 18% on shareholder equity"), and any concerns.
4. **Vibe Check.** Two stocks side-by-side. Pick the one you'd rather own.
   Repeat five times. We tell you what fraction agreed with your saved style.
5. **See what I learned about you.** Your style rendered as a real ASCII
   flowchart, with each node and rule connected by branching lines.

Press `Ctrl+M` to switch to Advanced mode and you'll see the full editor,
where you can change any rule, save it as a new version, and roll back.

---

## Technical architecture

For the technically curious — here's how Chamak is built.

### The data model

The primary object is a **MindMap** (called "Investing Style" in the UI). A
MindMap is a graph of:

- **Nodes**: portfolio goals, beliefs, metrics, sectors, etc.
- **Edges**: typed relationships (`supports`, `contradicts`, `requires`,
  `strengthens`, `weakens`, `depends_on`).
- **Rules**: machine-evaluable predicates bound to belief nodes.

Each save of a MindMap is an immutable snapshot stored in
`mindmap_versions.graph_json`. Diffs are computed on demand by comparing
snapshots. Restore = save the older snapshot as the new latest.

### Rules

Rules are a small DSL — `debt_to_equity < 0.5 AND roe > 15`. The parser is a
hand-written tokenizer + recursive-descent parser that builds a **typed,
closed AST**:

```
Comparison · Between · And · Or · Not · MetricRef · Literal
```

There is no `eval` / `exec` anywhere in the codebase. The evaluator is a
hand-written interpreter over the AST. It uses **soft sigmoid thresholds**,
so a stock that just misses a rule still scores ~0.5 instead of a hard zero
— much more useful in practice than yes/no logic.

### Scoring

```
score(stock, mindmap) = Σ_r ( w_r · sat_r · conf_r ) / Σ_r ( w_r · conf_r )
```

- `sat_r` ∈ [0, 1] = soft satisfaction of rule r
- `w_r`            = weight on the rule
- `conf_r`         = our confidence in the rule

Hard rules (marked as "deal-breakers") gate the whole score to 0 if they
fail. Polarity-inverted rules ("avoid expensive stocks") flip the
satisfaction at score time.

### Storage

SQLite with the JSON1 extension. The whole database is one file in the
user's data directory (`~/.local/share/chamak/chamak.db` on Linux,
`%APPDATA%\chamak\chamak.db` on Windows, `~/Library/Application
Support/chamak/chamak.db` on macOS). WAL mode enabled for safety.

No external services. No accounts. No cloud. Everything runs locally.

### TUI rendering

Built on **Textual**. The flowchart and candlestick chart are both
hand-written ASCII renderers that emit Rich-markup strings — no external
dependencies for either. The candle renderer detects each candle's color
(green/red) and compresses adjacent same-color cells into single markup
spans so Rich's parser stays happy.

### LLM (optional)

Chamak works completely without an internet connection. If you set the
environment variable `OPENROUTER_API_KEY`, Chamak can use an LLM to:

- Extract candidate rules from a narrative ("I prefer companies that have
  survived multiple economic cycles")
- Suggest follow-up interview questions

LLMs are **never** used for scoring, ranking, predicting prices, or anything
that touches a number that ends up in the recommendation engine.

---

## Tech stack

| Layer         | What we used                               | Why                              |
|---------------|--------------------------------------------|----------------------------------|
| Language      | Python 3.12                                | rich ecosystem, fast iteration   |
| Package mgmt  | [uv](https://github.com/astral-sh/uv)      | fast, cross-platform installer   |
| TUI framework | [Textual](https://textual.textualize.io/)  | full async TUI w/ CSS-like styles|
| Data models   | pydantic v2                                | validated, typed domain objects  |
| Graph engine  | networkx                                   | DiGraph for in-memory mind maps  |
| Storage       | SQLite + JSON1                             | one-file local DB, no setup      |
| CLI           | Typer                                      | nice argparse layer with help    |
| Market data   | yfinance                                   | free Indian-market price data    |
| HTTP          | httpx                                      | LLM API calls                    |
| YAML          | PyYAML                                     | interview script format          |
| Terminal      | Rich                                       | markup + color rendering         |
| Testing       | pytest + pytest-asyncio                    | 82 tests, including TUI smoke    |
| Linting       | ruff                                       | one tool, fast                   |

Hand-written in-house: the ASCII flowchart renderer, the ASCII candlestick
renderer, the rule AST + parser + soft-threshold evaluator, the plain-English
rule translator, the verdict tier system, and the explainability engine.

---

## Project layout

```
chamak/
├── pyproject.toml               build + dependencies
├── README.md                    this file
├── src/chamak/
│   ├── config.py                paths, settings, mode preference
│   ├── cli.py                   `chamak` command (typer)
│   ├── core/                    domain models + ids + errors
│   ├── storage/                 SQLite + migrations + repositories
│   ├── graph/                   MindMapGraph (networkx) + diff
│   ├── rules/                   AST, parser, metric registry, evaluator,
│   │                            plain-English translator
│   ├── interview/               YAML script + state machine + archetype
│   ├── market_data/             yfinance adapter, ticker map, cache
│   ├── news/                    sentiment classifier + storage
│   ├── scoring/                 weighted-rule compatibility scoring
│   ├── recommendation/          ranker
│   ├── portfolio/               drift / contradiction detector
│   ├── explain/                 plain renderer + verdict tiers
│   ├── llm/                     LLMClient protocol + OpenRouter + Null
│   ├── demo/                    seed data + prebuilt styles + price gen
│   └── tui/
│       ├── app.py               the Textual app, mode-aware boot
│       ├── theme.py             grayscale theme with accent colors
│       ├── widgets/
│       │   ├── flowchart.py     ASCII mind-map renderer
│       │   ├── candle.py        ASCII candlestick + sparkline
│       │   ├── score_bar.py     progress-bar style fit display
│       │   └── banner.py        block ASCII Chamak logo
│       ├── screens/             Advanced-mode screens
│       └── simple/              Simple-mode screens
├── data/
│   └── nifty50.json             bundled ticker universe
└── tests/                       82 tests
```

---

## Testing

```bash
uv run pytest -q
```

82 tests covering: the rule compiler (edge cases like missing metrics,
hard-rule gating, polarity inversion), scoring formulas, graph diffing,
schema migrations, the interview state machine, every TUI screen (mount
without errors), the autopilot walkthrough, the candlestick renderer, the
flowchart renderer, the plain-English translator, the verdict tiers, the
demo seeder, and a full end-to-end "is the demo recordable right now?"
rehearsal test.

```bash
uv run pytest tests/test_demo_recording.py -v
```

Run that before any screen recording — it seeds the data, scores against
every prebuilt style, asserts the top results match the script, and boots
the autopilot through every scene.

---

## Credits

- **Toeesh Chaudhary** (12th A) — design, architecture, implementation.
- **Harsh Sharma** (12th A) — testing, ideas, feedback.
- a tiny bit of openai's models for creating this same documentation that you are reading.
---

*Chamak is built for learning, not for live trading. Numbers in the demo
mode are illustrative only.*
