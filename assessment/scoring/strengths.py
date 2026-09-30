"""Strengths scoring by win rate rather than raw hit count.

A theme's score is how much it was preferred out of how often it was offered.
"Preferred" is graduated, not a single click on one of the two statements —
the answer can land anywhere between them — so a theme's win is the fraction
of the answer that fell on its side (1.0 at the extreme, 0.5 for "autant
l'une que l'autre", down to 0.0 at the other extreme), summed over every
exposure. This is a strict generalisation of a plain win/loss count: an
answer recorded before the graduated scale existed is still exactly
"option_a" or "option_b" and still contributes a full 1.0/0.0, so old results
score identically to before. Counting raw hits would make the ranking partly
a property of the item pool whenever exposure is uneven across themes, and
options can carry more than one tag, so a single answer could otherwise award
more than one point to some themes and not others. Domains and how many
themes count as "top" / "bottom" are derived from whatever `themes` dict is
passed in, so this file has no knowledge of any particular taxonomy — swap
the data, keep the scoring.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult, bipolar_weight


def _domains_of(themes: dict) -> list[str]:
    """Domain names in first-appearance order, so percentage breakdowns and
    legends stay in a stable, deliberate order rather than alphabetical."""
    seen: list[str] = []
    for theme in themes.values():
        domain = theme["domain"]
        if domain not in seen:
            seen.append(domain)
    return seen


def score(items: Sequence[dict], answers: dict[str, str], themes: dict) -> ModuleResult:
    exposure: dict[str, int] = {t: 0 for t in themes}
    wins: dict[str, int] = {t: 0 for t in themes}
    evidence: dict[str, list[dict]] = {t: [] for t in themes}

    for item in items:
        chosen = answers.get(item["id"])
        if chosen is None:
            continue
        offered = {
            option: [t for t in item["alignment"].get(option, []) if t in themes]
            for option in ("option_a", "option_b")
        }
        for option, tags in offered.items():
            weight = bipolar_weight(chosen, option)
            for theme in tags:
                exposure[theme] += 1
                wins[theme] += weight
                evidence[theme].append({
                    "id": item["id"],
                    "question": item["question"],
                    "text": item[option],
                    "chosen": weight >= 0.5,
                    "weight": weight,
                })

    rates: dict[str, float] = {}
    errors: dict[str, float] = {}
    for theme in themes:
        n = exposure[theme]
        if n == 0:
            rates[theme] = 0.0
            errors[theme] = 0.0
            continue
        p = wins[theme] / n
        rates[theme] = round(p, 4)
        errors[theme] = round(math.sqrt(p * (1 - p) / n), 4)

    ranking = sorted(
        themes,
        key=lambda t: (-rates[t], -wins[t], -exposure[t], t),
    )

    # A "top five" only makes sense once there are meaningfully more than five
    # themes to rank; with a smaller taxonomy the top/bottom bands shrink so
    # they never overlap or eat the whole list.
    top_n = min(5, len(ranking))
    bottom_n = min(3, len(ranking) - top_n)
    top = ranking[:top_n]
    bottom = ranking[len(ranking) - bottom_n:] if bottom_n else []
    supporting = ranking[top_n:len(ranking) - bottom_n] if bottom_n else ranking[top_n:]

    # Anything statistically level with the last "top" theme belongs in the
    # same cluster; claiming a clean cut over a tie would be false precision.
    tied_with_fifth: list[str] = []
    if len(ranking) > top_n:
        anchor = ranking[top_n - 1]
        for theme in ranking[top_n:]:
            pooled = math.sqrt(errors[anchor] ** 2 + errors[theme] ** 2)
            if pooled == 0 or abs(rates[anchor] - rates[theme]) <= pooled:
                tied_with_fifth.append(theme)
            else:
                break

    domains = _domains_of(themes)
    domain_rates = {}
    for domain in domains:
        members = [t for t in themes if themes[t]["domain"] == domain]
        domain_rates[domain] = sum(rates[t] for t in members) / len(members) if members else 0.0
    total = sum(domain_rates.values())
    n_domains = len(domains) or 1
    domain_pct = {
        d: round((v / total * 100.0) if total else 100.0 / n_domains, 1)
        for d, v in domain_rates.items()
    }

    return ModuleResult(
        module_id="strengths",
        summary={
            "ranking": ranking,
            "win_rates": rates,
            "wins": wins,
            "exposure": exposure,
            "standard_error": errors,
            "top": top,
            "supporting": supporting,
            "bottom": bottom,
            "tied_with_fifth": tied_with_fifth,
            "domain_percentages": domain_pct,
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
