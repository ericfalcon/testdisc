"""Core data types shared by sampling, scoring and reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Kept short: these are laid out as a horizontal scale, five across.
LIKERT_OPTIONS = (
    "Pas du tout d'accord",
    "Pas d'accord",
    "Neutre",
    "D'accord",
    "Tout à fait d'accord",
)

# A "forced_choice" item still compares exactly two statements, but the answer
# is graduated rather than a single click on one of them — the same five-point
# logic as LIKERT_OPTIONS, anchored to "the statement above" / "the statement
# below" instead of an agreement scale. BIPOLAR_VALUES are what gets stored in
# an answer, in the same order as the labels; the two extremes are spelled
# "option_a"/"option_b" on purpose, so an export saved before this scale
# existed (a plain, unweighted pick) still loads and scores exactly as it did
# before — this is a strict generalisation of the old binary choice, not a
# rescoring of it.
BIPOLAR_LABELS = (
    "Complètement la phrase du haut",
    "Plutôt la phrase du haut",
    "Autant l'une que l'autre",
    "Plutôt la phrase du bas",
    "Complètement la phrase du bas",
)
BIPOLAR_VALUES = ("option_a", "lean_a", "neutral", "lean_b", "option_b")
BIPOLAR_WEIGHTS: dict[str, tuple[float, float]] = {
    "option_a": (1.0, 0.0),
    "lean_a": (0.75, 0.25),
    "neutral": (0.5, 0.5),
    "lean_b": (0.25, 0.75),
    "option_b": (0.0, 1.0),
}


def bipolar_weight(value: str, option: str) -> float:
    """Share of a graduated forced-choice answer that goes to ``option``
    ("option_a" or "option_b"). Unknown/legacy values fall back to whichever
    extreme they name, so a value that is literally "option_a" or "option_b"
    (every answer recorded before this scale existed) behaves exactly as the
    old all-or-nothing scoring did."""
    weight_a, weight_b = BIPOLAR_WEIGHTS.get(
        value, (1.0, 0.0) if value == "option_a" else (0.0, 1.0)
    )
    return weight_a if option == "option_a" else weight_b


@dataclass(frozen=True)
class Item:
    """One question as presented to the user.

    ``uid`` is unique across the whole session and is what answers are keyed by.
    The adaptive DISC module re-presents the same source stems under a different
    frame, so the source id alone would collide.
    """

    uid: str
    module_id: str
    kind: str  # "likert5" | "forced_choice"
    prompt: str
    source: dict[str, Any]
    frame: str = ""  # optional context line shown above the prompt
    options: tuple[str, ...] = ()

    @property
    def source_id(self) -> str:
        return self.source["id"]


@dataclass
class ModuleResult:
    """Scored output of one module."""

    module_id: str
    summary: dict[str, Any] = field(default_factory=dict)
    detail: dict[str, Any] = field(default_factory=dict)


def adjust(response: int, keyed: int) -> int:
    """Flip a reverse-keyed response onto the forward scale."""
    return response if keyed >= 0 else 6 - response


def and_join(names: list[str]) -> str:
    """A French-style enumeration: 'A', 'A et B', 'A, B et C' — never the bare
    comma-separated list a naive join() produces, which reads as a fragment
    rather than a full French list. Shared by the report narrative and the
    trainer Sheet export, which both list module results (top themes, top
    drivers, ...) inside French sentences or cells."""
    if len(names) <= 1:
        return ", ".join(names)
    return ", ".join(names[:-1]) + " et " + names[-1]


_VOWELS = "aeiouàâéèêëîïôùûü"


def de_prefix(word: str) -> str:
    """The preposition that goes before ``word`` — "de " normally, "d’" when
    ``word`` starts with a vowel sound ("d’Autonomie", not "de Autonomie").
    Works just as well on a whole and_join() list, since only the first word
    of the list decides the elision ("d’Autonomie, Reconnaissance et Lien")."""
    return "d’" if word[:1].lower() in _VOWELS else "de "


def de(word: str) -> str:
    """"de Sécurité" but "d’Autonomie" — the full elided phrase."""
    return f"{de_prefix(word)}{word}"
