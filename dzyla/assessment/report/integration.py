"""Cross-module sections. These only exist when more than one lens was completed
and are the reason for doing more than the core."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES
from ..scoring.stress import MODE_BLURBS, MODE_LABELS, MODE_TO_STYLE

# Which DISC dimension each strength theme leans on. Used to find where a
# person's strengths pull against their behavioural default.
THEME_AFFINITY = {
    "Achiever": "D", "Activator": "D", "Adaptability": "S", "Analytical": "C",
    "Arranger": "C", "Belief": "S", "Command": "D", "Communication": "I",
    "Competition": "D", "Connectedness": "S", "Consistency": "C", "Context": "C",
    "Deliberative": "C", "Developer": "S", "Discipline": "C", "Empathy": "S",
    "Focus": "D", "Futuristic": "I", "Harmony": "S", "Ideation": "I",
    "Includer": "I", "Individualization": "I", "Input": "C", "Intellection": "C",
    "Learner": "C", "Maximizer": "C", "Positivity": "I", "Relator": "S",
    "Responsibility": "C", "Restorative": "C", "Self-Assurance": "D",
    "Significance": "I", "Strategic": "D", "Woo": "I",
}


def _verb(names: list[str], singular: str, plural: str) -> str:
    return singular if len(names) == 1 else plural


def disc_x_strengths(disc_result, strengths_result) -> dict | None:
    d = disc_result.summary
    primary, lowest = d["primary"], d["lowest"]
    top = strengths_result.summary["top"]

    reinforcing = [t for t in top if THEME_AFFINITY.get(t) == primary]
    conflicting = [t for t in top if THEME_AFFINITY.get(t) == lowest]

    lines = []
    if reinforcing:
        lines.append(
            f"<b>Reinforcing:</b> {', '.join(reinforcing)} "
            f"{_verb(reinforcing, 'leans', 'lean')} on {STYLE_NAMES[primary]}, "
            f"which is already your strongest dimension. This is where you are most reliably "
            f"yourself — and where you will be least inclined to check your own judgement."
        )
    if conflicting:
        lines.append(
            f"<b>Pulling against you:</b> {', '.join(conflicting)} "
            f"{_verb(conflicting, 'draws', 'draw')} on "
            f"{STYLE_NAMES[lowest]}, your <i>lowest</i> dimension. You value this way of working "
            f"and it is not how you behave by default. Expect it to show up in your intentions "
            f"more than in your calendar, and expect that gap to be visible to colleagues."
        )
    if not lines:
        lines.append(
            f"Your signature themes spread across dimensions rather than concentrating on "
            f"{STYLE_NAMES[primary]}. That makes you harder to predict, and harder to pigeonhole."
        )
    return {"title": "Behaviour vs. strengths", "icon": "\U0001f501", "lines": lines}


def strain_x_stress(strain: dict | None, stress_result) -> dict | None:
    if strain is None or stress_result is None:
        return None
    mode = stress_result.summary["dominant"]
    lines = [
        f"Sous charge, votre mode dominant est <b>{MODE_LABELS[mode]}</b>. {MODE_BLURBS[mode]}"
    ]
    if strain["band"] == "high":
        lines.append(
            f"Vous portez aussi une <b>charge d'adaptation élevée</b> (indice de tension "
            f"{strain['index']:.0f}) : votre profil au travail s'écarte nettement de votre profil "
            f"naturel, surtout sur {STYLE_NAMES[strain['largest']]}. Une adaptation soutenue combinée "
            f"à une réponse de type « {MODE_LABELS[mode].lower()} » sous pression est la combinaison "
            f"qui précède souvent l'épuisement — non parce que l'une ou l'autre serait malsaine en soi, "
            f"mais parce que la récupération doit bien venir de quelque part, et que le poste ne "
            f"l'apporte pas."
        )
    elif strain["band"] == "moderate":
        lines.append(
            f"Votre charge d'adaptation est modérée (indice {strain['index']:.0f}), concentrée sur "
            f"{STYLE_NAMES[strain['largest']]}. C'est le coût normal d'un poste plutôt qu'un signal "
            f"d'alerte, mais ça vaut la peine de savoir quelle partie du travail la génère."
        )
    else:
        lines.append(
            f"Votre charge d'adaptation est faible (indice {strain['index']:.0f}). Votre poste vous "
            f"demande largement un comportement que vous produisez de toute façon naturellement — une "
            f"forme d'adéquation réelle, et souvent sous-estimée."
        )
    return {"title": "Tension et pression", "icon": "⚡", "lines": lines}


def stress_x_disc(disc_result, stress_result) -> dict | None:
    if stress_result is None:
        return None
    mode = stress_result.summary["dominant"]
    expected = MODE_TO_STYLE[mode]
    primary = disc_result.summary["primary"]
    if expected == primary:
        line = (
            f"Votre mode sous pression est la version amplifiée de votre style naturel : vous devenez "
            f"<b>encore plus</b> ce que vous êtes déjà. Vos collègues voient une version intensifiée de "
            f"quelqu'un qu'ils reconnaissent, ce qui leur est plus facile que l'inverse — mais cela "
            f"signifie aussi que votre angle mort habituel s'aiguise précisément quand c'est le plus "
            f"risqué."
        )
    else:
        line = (
            f"Sous pression, vous changez de registre : votre dimension naturelle est "
            f"{STYLE_NAMES[primary]}, mais votre mode sous pression est <b>{MODE_LABELS[mode]}</b>, la "
            f"version amplifiée de {STYLE_NAMES[expected]}. Les personnes qui connaissent votre version "
            f"posée ne reconnaissent pas votre version sous tension. Ce décalage mérite d'être nommé à "
            f"votre équipe à l'avance, sans quoi elle risque de lire ce changement comme quelque chose "
            f"qui les concerne personnellement."
        )
    return {"title": "Qui vous devenez sous charge", "icon": "\U0001f329", "lines": [line]}


def motivators_x_role(motivator_result, strain: dict | None) -> dict | None:
    if motivator_result is None:
        return None
    top = motivator_result.summary["top"]
    bottom = motivator_result.summary["bottom"]
    lines = [
        f"Vous avez systématiquement fait le choix de <b>{', '.join(top)}</b>, au détriment de "
        f"<b>{', '.join(bottom)}</b> quand il fallait trancher. Ce sont ces arbitrages, pas votre "
        f"intitulé de poste, qui décideront si un rôle vaut la peine d'y rester."
    ]
    if strain and strain["band"] == "high":
        lines.append(
            "Au regard de votre charge d'adaptation élevée, la question à se poser est de savoir si le "
            "poste vous paie dans la monnaie que vous avez réellement choisie ici. Un effort "
            "supplémentaire est acceptable quand il achète vos moteurs principaux, et coûteux quand ce "
            "n'est pas le cas."
        )
    return {"title": "Ce que vous achetez réellement", "icon": "\U0001f9f2", "lines": lines}
