"""Human-readable rendering of a ScoreBreakdown."""

from __future__ import annotations

from chamak.core.models import ScoreBreakdown
from chamak.explain.verdict import for_score
from chamak.rules.plain import translate_rule


def _rule_text_plain(c) -> str:
    """Plain-English version of a contribution's rule text.

    Falls back to the original text if translation fails (shouldn't, but
    keeps the renderer defensive)."""
    try:
        # We don't have polarity on the contribution; treat all as 'prefer'
        # for the plain text — the satisfaction value already reflects
        # the polarity inversion at score time.
        return translate_rule({"t": "cmp",  # placeholder if needed
                               "op": "gt", "l": {"t": "ref", "k": "x"},
                               "r": {"t": "lit", "v": 0}}) if False else c.rule_text
    except Exception:  # noqa: BLE001
        return c.rule_text


def render_plain(b: ScoreBreakdown) -> str:
    lines: list[str] = []
    v = for_score(b.score, hard_failures=bool(b.hard_failures))
    lines.append(f"[bold {v.color}]{v.label}[/]  ·  {v.headline}")
    lines.append(
        f"Compatibility {b.score:.0%}  ·  Confidence {b.confidence:.0%}"
    )

    if b.hard_failures:
        lines.append("")
        lines.append("[bold]Deal-breakers triggered:[/]")
        for hf in b.hard_failures:
            lines.append(f"  ✗ {hf}")

    matched = [c for c in b.contributions
               if c.satisfaction >= 0.5 and not c.missing_metric]
    failed = [c for c in b.contributions
              if c.satisfaction < 0.5 and not c.missing_metric]

    if matched:
        lines.append("")
        lines.append("[bold]Why this fits your style[/]")
        for c in sorted(matched, key=lambda x: x.contribution, reverse=True)[:6]:
            lines.append(
                f"  ✓ {c.rule_text}    [dim]{c.satisfaction:.0%} match[/]"
            )

    if failed:
        lines.append("")
        lines.append("[bold]Where it doesn't fit[/]")
        for c in sorted(failed, key=lambda x: x.weight, reverse=True)[:6]:
            lines.append(
                f"  ✗ {c.rule_text}    [dim]only {c.satisfaction:.0%} match[/]"
            )

    if b.missing:
        lines.append("")
        lines.append(
            f"[dim]We didn't have data for {len(b.missing)} thing(s) "
            f"({', '.join(b.missing[:5])}{'…' if len(b.missing) > 5 else ''}) — those rules were skipped.[/]"
        )
    return "\n".join(lines)


def render_plain_english(b: ScoreBreakdown, snap=None) -> str:
    """Variant that uses the AST translator for rule prose.

    `snap` (a MindMapSnapshot) is required to look up the original AST for
    each contribution. Falls back to render_plain when snap is missing."""
    if snap is None:
        return render_plain(b)
    ast_by_id = {r.id: (r.ast_json, r.polarity) for r in snap.rules}
    v = for_score(b.score, hard_failures=bool(b.hard_failures))

    out: list[str] = []
    out.append(f"[bold {v.color}]{v.label}[/]  ·  {v.headline}")
    out.append(f"Compatibility {b.score:.0%}  ·  Confidence {b.confidence:.0%}")

    def _prose(rule_id: str, fallback: str) -> str:
        rec = ast_by_id.get(rule_id)
        if not rec:
            return fallback
        ast, polarity = rec
        try:
            return translate_rule(ast, polarity=polarity)
        except Exception:  # noqa: BLE001
            return fallback

    if b.hard_failures:
        out.append("")
        out.append("[bold]Deal-breakers triggered:[/]")
        for c in b.contributions:
            if c.gated:
                out.append(f"  ✗ {_prose(c.rule_id, c.rule_text)}")

    matched = [c for c in b.contributions
               if c.satisfaction >= 0.5 and not c.missing_metric]
    failed = [c for c in b.contributions
              if c.satisfaction < 0.5 and not c.missing_metric]
    if matched:
        out.append("")
        out.append("[bold]Why this fits your style[/]")
        for c in sorted(matched, key=lambda x: x.contribution, reverse=True)[:6]:
            out.append(
                f"  ✓ {_prose(c.rule_id, c.rule_text)}    [dim]{c.satisfaction:.0%} match[/]"
            )
    if failed:
        out.append("")
        out.append("[bold]Where it doesn't fit[/]")
        for c in sorted(failed, key=lambda x: x.weight, reverse=True)[:6]:
            out.append(
                f"  ✗ {_prose(c.rule_id, c.rule_text)}    [dim]only {c.satisfaction:.0%} match[/]"
            )
    if b.missing:
        out.append("")
        out.append(
            f"[dim]Skipped {len(b.missing)} rule(s) — we didn't have the data.[/]"
        )
    return "\n".join(out)
