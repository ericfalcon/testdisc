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
        "matérielle au quotidien : le corps, l'espace, les ressources, une routine qui tient. "
        "Vous remarquez vite ce qui menace cet équilibre — un imprévu, une dépense, une "
        "fatigue qui s'installe — et vous ajustez votre environnement avant que la gêne ne "
        "devienne un vrai problème. Cette vigilance discrète passe souvent inaperçue des "
        "autres, précisément parce qu'elle fonctionne : le confort qu'elle produit semble "
        "aller de soi."
    ),
    "Social": (
        "Votre attention va en premier vers le groupe : votre place dedans, sa dynamique, "
        "votre contribution à quelque chose de plus grand que vous. Vous repérez vite qui a "
        "de l'influence, qui est mis à l'écart, où se situent les alliances — une lecture "
        "sociale qui vous aide à vous positionner utilement dans presque n'importe quel "
        "collectif. Le revers, c'est une attention presque permanente à votre statut dans le "
        "groupe, parfois au détriment d'un lien individuel qui mériterait plus de votre temps."
    ),
    "Sexuel": (
        "Votre attention va en premier vers l'intensité d'un lien en particulier : la "
        "connexion, l'alchimie, être choisi par quelqu'un plutôt qu'accepté par tous. Vous "
        "cherchez naturellement ce qui va créer une intensité entre vous et une personne, une "
        "idée ou une situation, plus qu'une approbation générale et diffuse. Cette recherche "
        "d'intensité peut donner à vos relations et à vos engagements une profondeur rare — "
        "mais aussi les rendre instables dès que l'intensité initiale retombe."
    ),
}

# Strengths / cost / growth edge for each instinct — added for the same reason
# the 9 Enneagram types carry them: a one-line blurb reads as thin once
# someone has taken the test and wants to actually think about the result.
INSTINCT_FORCES = {
    "Conservation": (
        "Sens pratique, fiabilité au quotidien, capacité à anticiper un besoin matériel avant "
        "qu'il ne devienne urgent, stabilité qui rassure un entourage moins organisé."
    ),
    "Social": (
        "Sens du collectif, lecture fine des dynamiques de groupe, capacité à fédérer, "
        "générosité envers une cause ou une communauté."
    ),
    "Sexuel": (
        "Capacité à créer une connexion forte rapidement, intensité et présence dans une "
        "relation, goût du risque relationnel, charisme dans le tête-à-tête."
    ),
}

INSTINCT_OVERUSE = {
    "Conservation": (
        "Vous consacrez une énergie disproportionnée à sécuriser un détail matériel mineur, "
        "au point de perdre de vue ce qui se joue autour de vous sur le plan relationnel ou "
        "collectif."
    ),
    "Social": (
        "Vous vous investissez dans le rôle que vous jouez au sein du groupe au point de "
        "négliger une relation individuelle qui compte pourtant réellement pour vous."
    ),
    "Sexuel": (
        "Vous perdez l'intérêt pour une relation ou un projet dès que l'intensité du début "
        "s'estompe, même quand ce qui reste est solide."
    ),
}

INSTINCT_DEVELOPPEMENT = {
    "Conservation": (
        "Remarquer, de temps en temps, ce qui se passe dans la pièce ou dans la relation "
        "avant de vérifier que tout est en ordre autour de vous."
    ),
    "Social": (
        "Accorder à une relation à deux la même attention pleine et entière que celle que "
        "vous donnez naturellement à la dynamique d'un groupe."
    ),
    "Sexuel": (
        "Rester engagé dans une relation ou un projet une fois l'intensité initiale retombée, "
        "plutôt que d'en chercher une nouvelle ailleurs."
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
