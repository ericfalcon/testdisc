"""Instinctual-subtype scoring over a full round robin of 3 instincts.

The 3 survival instincts — conservation (self-preservation), social,
sexuel/un-à-un (one-to-one) — are a layer the Narrative Enneagram tradition
(Helen Palmer & David Daniels) puts real weight on alongside the 9 base
types, not a replacement for them: the same person can be, say, a
Perfectionniste social or a Perfectionniste sexuel, and the flavour differs.
The concept itself predates any one school (it goes back to Naranjo) and
belongs to no one; only the exact wording below is original to this app.

Same win-rate mechanics as motivators.py: every instinct meets every other
exactly once per round, repeated for stability, so exposure is equal by
construction and the win rate needs no correction.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult

INSTINCTS = ("Conservation", "Social", "Sexuel")

INSTINCT_LABELS = {
    "Conservation": "Conservation",
    "Social": "Social",
    "Sexuel": "Sexuel (un-à-un)",
}

INSTINCT_BLURBS = {
    "Conservation": (
        "Votre attention va en premier vers ce qui assure votre confort et votre sécurité "
        "matérielle au quotidien : le corps, l'espace, les ressources, une routine qui tient."
    ),
    "Social": (
        "Votre attention va en premier vers le groupe : votre place dedans, sa dynamique, "
        "votre contribution à quelque chose de plus grand que vous."
    ),
    "Sexuel": (
        "Votre attention va en premier vers l'intensité d'un lien en particulier : la "
        "connexion, l'alchimie, être choisi par quelqu'un plutôt qu'accepté par tous."
    ),
}


def score(items: Sequence[dict], answers: dict[str, str]) -> ModuleResult:
    wins = {d: 0 for d in INSTINCTS}
    exposure = {d: 0 for d in INSTINCTS}
    evidence: dict[str, list[dict]] = {d: [] for d in INSTINCTS}

    for item in items:
        chosen = answers.get(item["id"])
        if chosen is None:
            continue
        for option in ("option_a", "option_b"):
            instinct = item["alignment"][option]
            if instinct not in wins:
                continue
            exposure[instinct] += 1
            picked = option == chosen
            wins[instinct] += 1 if picked else 0
            other = item["alignment"]["option_b" if option == "option_a" else "option_a"]
            evidence[instinct].append({
                "id": item["id"],
                "text": item[option],
                "against": other,
                "chosen": picked,
            })

    rates = {
        d: round(wins[d] / exposure[d], 4) if exposure[d] else 0.0 for d in INSTINCTS
    }
    errors = {
        d: round(math.sqrt(rates[d] * (1 - rates[d]) / exposure[d]), 4) if exposure[d] else 0.0
        for d in INSTINCTS
    }
    ranking = sorted(INSTINCTS, key=lambda d: (-rates[d], d))

    return ModuleResult(
        module_id="enneagram_instinct",
        summary={
            "win_rates": rates,
            "wins": wins,
            "exposure": exposure,
            "standard_error": errors,
            "ranking": ranking,
            "dominant": ranking[0],
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
