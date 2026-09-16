"""Motivator scoring over a round-robin of forced-choice pairs.

Every driver meets every other driver exactly once, so exposure is equal by
construction and the win rate needs no correction.
"""

from __future__ import annotations

import math
from typing import Sequence

from ..types import ModuleResult

DRIVERS = (
    "Autonomie", "Maîtrise", "Reconnaissance", "Sécurité",
    "Sens", "Lien", "Statut", "Variété",
)

DRIVER_BLURBS = {
    "Autonomie": "La liberté de choisir votre méthode et d'être jugé sur le résultat.",
    "Maîtrise": "Faire des progrès visibles sur quelque chose de difficile.",
    "Reconnaissance": "Voir son travail reconnu, précisément et personnellement, par des gens dont on respecte le jugement.",
    "Sécurité": "Un socle stable : des exigences prévisibles et un poste qui sera toujours là.",
    "Sens": "Un travail dont vous croyez le bien-fondé, au-delà du travail lui-même.",
    "Lien": "Appartenir à un groupe de personnes avec qui vous aimez sincèrement travailler.",
    "Statut": "Une position et une influence réelles sur les décisions qui comptent.",
    "Variété": "Assez de changement pour que le problème reste intéressant.",
}


def score(items: Sequence[dict], answers: dict[str, str]) -> ModuleResult:
    wins = {d: 0 for d in DRIVERS}
    exposure = {d: 0 for d in DRIVERS}
    evidence = {d: [] for d in DRIVERS}

    for item in items:
        chosen = answers.get(item["id"])
        if chosen is None:
            continue
        for option in ("option_a", "option_b"):
            driver = item["alignment"][option]
            if driver not in wins:
                continue
            exposure[driver] += 1
            picked = option == chosen
            wins[driver] += 1 if picked else 0
            other = item["alignment"]["option_b" if option == "option_a" else "option_a"]
            evidence[driver].append({
                "id": item["id"],
                "text": item[option],
                "against": other,
                "chosen": picked,
            })

    rates = {
        d: round(wins[d] / exposure[d], 4) if exposure[d] else 0.0 for d in DRIVERS
    }
    errors = {
        d: round(math.sqrt(rates[d] * (1 - rates[d]) / exposure[d]), 4) if exposure[d] else 0.0
        for d in DRIVERS
    }
    ranking = sorted(DRIVERS, key=lambda d: (-rates[d], d))

    return ModuleResult(
        module_id="motivators",
        summary={
            "win_rates": rates,
            "wins": wins,
            "exposure": exposure,
            "standard_error": errors,
            "ranking": ranking,
            "top": ranking[:3],
            "bottom": ranking[-2:],
        },
        detail={"evidence": evidence, "item_ids": [i["id"] for i in items]},
    )
