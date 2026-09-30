"""Declarative registry of assessment modules.

Adding a lens means adding an entry here plus its data and scorer. The runner,
the picker, the results page and the export all work off this table, so none of
them need to know which modules exist.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable

from . import items as pools
from .scoring import disc, instincts, motivators, strengths, stress
from .types import Item, ModuleResult

# L'ennéagramme n'est pas une évaluation commerciale : ses 9 types et ses trois
# centres (Corps, Cœur, Tête) sont un cadre public partagé par de nombreuses
# écoles, sans nomenclature déposée unique. Le référentiel et les items
# ci-dessous (data/enneagram_types.json, data/enneagram_items.json) sont une
# formulation originale de ce cadre, pas la reprise d'un test existant (par
# exemple le RHETI de Riso-Hudson, qui lui est protégé).

NATURAL_FRAME = (
    "Répondez tel que vous êtes quand rien de particulier ne vous sollicite — "
    "en dehors du travail, dans votre état le plus naturel."
)
ADAPTIVE_FRAME = (
    "Mêmes affirmations, cadre différent : répondez pour votre poste actuel — "
    "comment vous vous comportez réellement au travail."
)
STRESS_FRAME = "Pensez à votre dernière semaine vraiment sous tension, pas à une semaine moyenne."
MOTIVATORS_FRAME = (
    "Les mêmes envies reviennent plusieurs fois, chaque fois face à une concurrente "
    "différente : c'est volontaire, c'est ce qui permet de les classer les unes par "
    "rapport aux autres — pas un bug."
)
STRENGTHS_FRAME = (
    "Les mêmes qualités reviennent plusieurs fois, chaque fois face à une autre : "
    "c'est volontaire, c'est ce qui permet de les classer les unes par rapport aux "
    "autres — pas un bug."
)
ENNEAGRAM_FRAME = (
    "Les mêmes tendances reviennent plusieurs fois, chaque fois face à une autre : "
    "c'est volontaire, c'est ce qui permet de les classer les unes par rapport aux "
    "autres — pas un bug."
)
INSTINCT_FRAME = (
    "Neuf phrases seulement : de quoi dégager celui des trois instincts qui capte le "
    "plus votre attention en premier, pas un profil détaillé en soi."
)


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    icon: str
    blurb: str
    kind: str  # "core" | "addon"
    item_type: str  # "likert5" | "forced_choice"
    build: Callable[[random.Random, str, dict], list[Item]]
    rebuild: Callable[[list[str], str], list[Item]]
    score: Callable[[list[Item], dict[str, Any], dict], ModuleResult]
    minutes: dict[str, int] = field(default_factory=lambda: {"standard": 5})
    variants: tuple[str, ...] = ("standard",)
    depends_on: tuple[str, ...] = ()
    variant_labels: dict[str, str] = field(default_factory=dict)

    def length(self, variant: str, context: dict | None = None) -> int:
        return len(self.build(random.Random(0), variant, context or {}))


def _answers_by_source(items: list[Item], answers: dict[str, Any]) -> dict[str, Any]:
    return {item.source_id: answers[item.uid] for item in items if item.uid in answers}


# --------------------------------------------------------------------------- DISC

def _build_disc_natural(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_likert_items(pools.sample_disc(rng), "disc_natural", NATURAL_FRAME)


def _score_disc(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return disc.score([i.source for i in items], _answers_by_source(items, answers))


def _build_disc_adaptive(rng: random.Random, variant: str, context: dict) -> list[Item]:
    """Repose exactement les mêmes affirmations que le passage naturel.

    Les deux profils ne sont comparables que si les items sont identiques,
    donc ce module réutilise les identifiants du module naturel plutôt que
    d'en tirer de nouveaux au hasard."""
    ids = context.get("disc_natural_item_ids") or [q["id"] for q in pools.sample_disc(rng)]
    return pools.rebuild_from_ids("disc_adaptive", "disc", ids, ADAPTIVE_FRAME)


# ------------------------------------------------------------------------- stress

def _build_stress(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_likert_items(pools.sample_stress(rng), "stress_profile", STRESS_FRAME)


def _score_stress(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return stress.score([i.source for i in items], _answers_by_source(items, answers))


# --------------------------------------------------------------------- motivators

def _build_motivators(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_choice_items(pools.sample_motivators(rng), "motivators", MOTIVATORS_FRAME)


def _score_motivators(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return motivators.score([i.source for i in items], _answers_by_source(items, answers))


# --------------------------------------------------------------------- strengths

def _build_strengths(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_choice_items(pools.sample_strengths(rng, 24), "strengths_core", STRENGTHS_FRAME)


def _score_strengths(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return strengths.score([i.source for i in items], _answers_by_source(items, answers), pools.strengths_themes())


# --------------------------------------------------------------------- enneagram

def _build_enneagram(rng: random.Random, variant: str, context: dict) -> list[Item]:
    return pools.to_choice_items(pools.sample_enneagram(rng, 24), "enneagram", ENNEAGRAM_FRAME)


def _score_enneagram(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    # Le score par taux de victoire est générique (voir scoring/strengths.py) :
    # il ne connaît rien du référentiel qu'on lui passe, donc il se réutilise
    # tel quel ici avec les 9 types en guise de "thèmes".
    result = strengths.score([i.source for i in items], _answers_by_source(items, answers), pools.enneagram_types())
    result.module_id = "enneagram"
    return result


# --------------------------------------------------------------------- instinct

def _build_instinct(rng: random.Random, variant: str, context: dict) -> list[Item]:
    # Only 9 items total (a full round robin over 3 instincts, repeated 3
    # times) — small enough that there is no sampling step, unlike the other
    # forced-choice modules: the whole pool is always used.
    return pools.to_choice_items(list(pools.instinct_items()), "enneagram_instinct", INSTINCT_FRAME)


def _score_instinct(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return instincts.score([i.source for i in items], _answers_by_source(items, answers))


def _rebuilder(kind: str, module_id: str, frame: str = "") -> Callable[[list[str], str], list[Item]]:
    def rebuild(ids: list[str], variant: str) -> list[Item]:
        return pools.rebuild_from_ids(module_id, kind, ids, frame)

    return rebuild


REGISTRY: dict[str, Module] = {}


def _register(module: Module) -> None:
    REGISTRY[module.id] = module


_register(Module(
    id="disc_natural",
    title="DISC — votre style naturel",
    icon="\U0001f9ed",
    blurb=(
        "Comment vous vous comportez naturellement : vos décisions, votre façon de "
        "communiquer, vos réactions face aux autres. Le module de base — il suffit pour "
        "la formation."
    ),
    kind="core",
    item_type="likert5",
    build=_build_disc_natural,
    rebuild=_rebuilder("disc", "disc_natural", NATURAL_FRAME),
    score=_score_disc,
    minutes={"standard": 5},
))

_register(Module(
    id="disc_adaptive",
    title="DISC — votre style au travail",
    icon="\U0001f3e2",
    blurb=(
        "Le même test, mais en pensant à votre poste actuel plutôt qu'à vous en général. "
        "Montre l'écart entre qui vous êtes et ce que le poste vous demande d'être."
    ),
    kind="addon",
    item_type="likert5",
    build=_build_disc_adaptive,
    rebuild=_rebuilder("disc", "disc_adaptive", ADAPTIVE_FRAME),
    score=_score_disc,
    minutes={"standard": 5},
    depends_on=("disc_natural",),
))

_register(Module(
    id="stress_profile",
    title="Sous pression",
    icon="⚡",
    blurb=(
        "Comment vous réagissez quand la pression monte vraiment : vous prenez le contrôle, "
        "vous insistez pour convaincre, vous encaissez en silence, ou vous vous repliez pour "
        "réfléchir."
    ),
    kind="addon",
    item_type="likert5",
    build=_build_stress,
    rebuild=_rebuilder("stress", "stress_profile", STRESS_FRAME),
    score=_score_stress,
    minutes={"standard": 3},
))

_register(Module(
    id="motivators",
    title="Ce qui vous motive",
    icon="\U0001f9f2",
    blurb=(
        "Ce qui vous donne — ou vous retire — l'envie de vous investir dans un poste : "
        "autonomie, reconnaissance, sécurité, sens, esprit d'équipe, statut, variété, maîtrise."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_motivators,
    rebuild=_rebuilder("motivators", "motivators", MOTIVATORS_FRAME),
    score=_score_motivators,
    minutes={"standard": 3},
))

# Le module "Forces" du projet d'origine reprenait le modèle des 34 thèmes CliftonStrengths
# de Gallup (une évaluation commerciale déposée) et est resté désactivé pour cette raison.
# Celui-ci le remplace avec un référentiel original : 12 thèmes en 4 domaines (Construire,
# Mobiliser, Relier, Éclairer), sans reprendre ni les noms ni le regroupement de Gallup — voir
# data/strengths_themes.json et data/strengths_items.json.
_register(Module(
    id="strengths_core",
    title="Vos forces naturelles",
    icon="\U0001f48e",
    blurb=(
        "Vos points forts naturels au travail, parmi 12 qualités réparties en 4 grandes "
        "familles : construire, mobiliser, relier, éclairer."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_strengths,
    rebuild=_rebuilder("strengths", "strengths_core", STRENGTHS_FRAME),
    score=_score_strengths,
    minutes={"standard": 4},
))

_register(Module(
    id="enneagram",
    title="Vos moteurs profonds (Ennéagramme)",
    icon="\U0001f300",
    blurb=(
        "Ce qui motive vos réactions en profondeur, au-delà du comportement observable : "
        "9 types répartis en 3 centres (Corps, Cœur, Tête). Complémentaire au DISC, pas "
        "un remplacement — le DISC décrit le comportement, l'ennéagramme la motivation "
        "derrière."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_enneagram,
    rebuild=_rebuilder("enneagram", "enneagram", ENNEAGRAM_FRAME),
    score=_score_enneagram,
    minutes={"standard": 4},
))

# Les 3 instincts de survie (conservation, social, sexuel/un-à-un) sont une
# couche sur le type de base, pas un remplacement — c'est la tradition
# narrative de l'ennéagramme (Helen Palmer & David Daniels, narrativeenneagram.org)
# qui y accorde une vraie place aux côtés des 9 types. Le concept lui-même
# précède toute école en particulier (Naranjo) et n'appartient à personne ;
# seule la formulation ci-dessous (data/instinct_items.json) est originale.
_register(Module(
    id="enneagram_instinct",
    title="Votre instinct dominant",
    icon="\U0001f9ec",
    blurb=(
        "Un complément rapide (9 questions) à l'Ennéagramme : lequel des 3 instincts de "
        "survie — conservation, social, ou sexuel (un-à-un) — capte le plus votre "
        "attention en premier. Le type dit ce qui vous motive ; l'instinct dit où ça se "
        "voit en premier."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_instinct,
    rebuild=_rebuilder("instincts", "enneagram_instinct", INSTINCT_FRAME),
    score=_score_instinct,
    minutes={"standard": 1},
    depends_on=("enneagram",),
))

CORE_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "core")
ADDON_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "addon")
