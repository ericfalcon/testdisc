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
from .scoring import disc
from .types import Item, ModuleResult

NATURAL_FRAME = (
    "Répondez tel que vous êtes quand rien de particulier ne vous sollicite — "
    "en dehors du travail, dans votre état le plus naturel."
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

# Remarque : les modules "strengths" (forces), "stress" et "motivators" du projet
# d'origine reprennent le modèle des 34 thèmes CliftonStrengths de Gallup, qui est
# une évaluation commerciale déposée. Ils ont été retirés de cette version française
# pour ne conserver que le module DISC, dont le contenu est original et libre de
# droits, et pour rester centré sur un test rapide (~10 minutes) adapté à un usage
# pré-formation. Le code de ces modules reste dans le dépôt (assessment/scoring,
# data/*.json) au cas où on voudrait les réactiver un jour avec un contenu propre.

CORE_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "core")
ADDON_MODULES = tuple(m.id for m in REGISTRY.values() if m.kind == "addon")
