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
from .scoring import disc, motivators, stress
from .types import Item, ModuleResult

NATURAL_FRAME = (
    "Répondez tel que vous êtes quand rien de particulier ne vous sollicite — "
    "en dehors du travail, dans votre état le plus naturel."
)
ADAPTIVE_FRAME = (
    "Mêmes affirmations, cadre différent : répondez pour votre poste actuel — "
    "comment vous vous comportez réellement au travail."
)
STRESS_FRAME = "Pensez à votre dernière semaine vraiment sous tension, pas à une semaine moyenne."


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
    return pools.to_choice_items(pools.sample_motivators(rng), "motivators")


def _score_motivators(items: list[Item], answers: dict[str, Any], context: dict) -> ModuleResult:
    return motivators.score([i.source for i in items], _answers_by_source(items, answers))


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
        "Quarante affirmations, réparties équitablement entre les quatre dimensions et "
        "mêlant des formulations positives et négatives afin de vérifier la cohérence du résultat."
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
        "Les mêmes quarante affirmations, répondues pour votre poste actuel. L'écart avec "
        "votre profil naturel est la tension que votre rôle vous demande."
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
        "Vingt affirmations sur une semaine vraiment sous tension, notées selon quatre modes "
        "de réaction : contrôle, persuasion, absorption, retrait."
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
        "Vingt-huit choix forcés portant sur huit moteurs. Chaque moteur affronte chacun des "
        "autres exactement une fois, donc rien n'est décidé par sa fréquence d'apparition."
    ),
    kind="addon",
    item_type="forced_choice",
    build=_build_motivators,
    rebuild=_rebuilder("motivators", "motivators"),
    score=_score_motivators,
    minutes={"standard": 4},
))

# Remarque : le module "strengths" (Forces) du projet d'origine reprend le modèle des 34
# thèmes CliftonStrengths de Gallup, qui est une évaluation commerciale déposée. Il reste
# désactivé dans cette version française pour cette raison — le diffuser publiquement, même
# traduit, exposerait à un risque de contrefaçon de marque. Le code reste dans le dépôt
# (assessment/scoring/strengths.py, data/strengths_*.json) en attendant un contenu original
# qui ne reprenne ni les noms de thèmes ni les domaines de Gallup.

CORE_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "core")
ADDON_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "addon")
