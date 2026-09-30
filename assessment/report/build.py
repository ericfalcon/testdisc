"""Assembles the full report from whichever modules were completed."""

from __future__ import annotations

from typing import Any

from .. import items as pools
from ..scoring import reliability
from ..scoring.disc import strain as disc_strain
from . import disc as disc_report
from . import integration, plan
from . import strengths as strengths_report

# The Enneagram's other two traditional heuristics, layered on top of the
# 9-type score: "wings" (the two numeric neighbours, which are always taken
# to flavour the base type) and the stress/security "arrows" — the same
# hexad (1-4-2-8-5-7-1) and triangle (3-9-6-3) already drawn on the wheel in
# app/components.py and app/plots.py, read as directed connections rather
# than a plain shape. The direction below (stress = forward along the
# arrow, security/growth = backward) is the one most widely reproduced
# across Enneagram teaching — a public-domain heuristic like the shape
# itself, not a claim tied to one school, and no more scientifically
# validated than the rest of this module.
_HEXAD = (1, 4, 2, 8, 5, 7, 1)
_TRIANGLE = (3, 9, 6, 3)


def _forward_edges(sequence: tuple[int, ...]) -> dict[int, int]:
    return {sequence[i]: sequence[i + 1] for i in range(len(sequence) - 1)}


_STRESS_BY_NUMBER = {**_forward_edges(_HEXAD), **_forward_edges(_TRIANGLE)}
_GROWTH_BY_NUMBER = {v: k for k, v in _STRESS_BY_NUMBER.items()}


def _wing_numbers(number: int) -> tuple[int, int]:
    return ((number - 2) % 9) + 1, (number % 9) + 1


def confidence_for(module_id: str, source_items: list[dict], answers: dict[str, Any]) -> dict | None:
    """Response-quality verdict for the Likert modules, which are the only ones
    with the forward/reverse structure the checks need."""
    group = {"disc_natural": "style", "disc_adaptive": "style", "stress_profile": "mode"}.get(module_id)
    if group is None:
        return None
    responses = [answers[i["id"]] for i in source_items if i["id"] in answers]
    return reliability.verdict(
        reliability.acquiescence(source_items, answers, group),
        reliability.split_half(source_items, answers, group),
        reliability.straight_lining(responses),
    )


def build_report(results: dict[str, Any], sources: dict[str, list[dict]],
                 answers: dict[str, dict[str, Any]]) -> dict:
    """`results` maps module id to ModuleResult; `sources` and `answers` are the
    raw item dicts and source-keyed answers used to compute response quality."""
    report: dict[str, Any] = {"sections": [], "integrations": []}

    confidence = {
        mid: confidence_for(mid, sources.get(mid, []), answers.get(mid, {}))
        for mid in results
    }
    report["confidence"] = {k: v for k, v in confidence.items() if v}

    disc_result = results.get("disc_natural")
    adaptive_result = results.get("disc_adaptive")
    strengths_result = results.get("strengths_core")
    stress_result = results.get("stress_profile")
    motivator_result = results.get("motivators")
    enneagram_result = results.get("enneagram")
    instinct_result = results.get("enneagram_instinct")

    disc_narrative = None
    if disc_result is not None:
        disc_narrative = disc_report.narrative(
            disc_result,
            confidence.get("disc_natural") or {"level": "Moderate"},
            pools.disc_descriptions(),
        )
        report["disc"] = disc_narrative

    strain = None
    if disc_result is not None and adaptive_result is not None:
        strain = disc_strain(disc_result, adaptive_result)
        report["strain"] = strain
        report["adaptive"] = adaptive_result.summary

    strengths_narrative = None
    if strengths_result is not None:
        strengths_narrative = strengths_report.narrative(strengths_result, pools.strengths_themes())
        report["strengths"] = strengths_narrative

    if stress_result is not None:
        report["stress"] = stress_result.summary
        report["stress_evidence"] = stress_result.detail["evidence"]

    if motivator_result is not None:
        report["motivators"] = motivator_result.summary
        report["motivator_evidence"] = motivator_result.detail["evidence"]

    if enneagram_result is not None:
        enneagram_types = pools.enneagram_types()
        report["enneagram"] = strengths_report.narrative(
            enneagram_result, enneagram_types,
            noun="type", nouns="types",
            bottom_note=(
                "Ces types arrivent en dernier non pas parce qu'ils vous décrivent mal, mais parce "
                "que vous ne les avez pas choisis quand une autre tendance était proposée en face. "
                "Ce sont ceux qui correspondent le moins à vos réflexes spontanés."
            ),
        )
        # The traditional 9-point circle needs every type's number and win rate,
        # not just the top/bottom bands narrative() keeps — kept separate so the
        # wheel and the ranked cards can each carry only what they need.
        report["enneagram"]["wheel"] = [
            {
                "name": name,
                "number": info["number"],
                "colour": info["badge_color"],
                "win_rate": enneagram_result.summary["win_rates"][name],
            }
            for name, info in enneagram_types.items()
        ]
        # A forced-choice score is a starting hypothesis, not a verdict — the
        # reference instruments in this field (e.g. the Narrative Enneagram's
        # own Stanford inventory) work by having the person read all 9 full
        # descriptions and pick the one that rings truest, rather than trust a
        # computed rank alone. All 9 go here so the report can offer that same
        # self-check next to the computed one — ordered by score (highest
        # first) so the list also doubles as the detailed version of the
        # ranking, rather than a traditional-number order disconnected from it.
        win_rates = enneagram_result.summary["win_rates"]
        report["enneagram"]["all_types"] = [
            {
                "name": name,
                "number": info["number"],
                "colour": info["badge_color"],
                "tagline": info["tagline"],
                "vision_du_monde": info["vision_du_monde"],
                "moteur_profond": info["moteur_profond"],
                "description": info["description"],
                "forces": info["forces"],
                "shadow": info["shadow"],
                "overuse": info["overuse"],
                "developpement": info["developpement"],
                "win_rate": win_rates[name],
            }
            for name, info in sorted(
                enneagram_types.items(), key=lambda kv: (-win_rates[kv[0]], kv[1]["number"])
            )
        ]

        # The dominant type (highest win rate) plus its two wings and its
        # stress/growth points — see the heuristic note above the maps.
        number_to_name = {info["number"]: name for name, info in enneagram_types.items()}

        def _brief(name: str) -> dict:
            info = enneagram_types[name]
            return {
                "name": name, "number": info["number"], "colour": info["badge_color"],
                "tagline": info["tagline"], "win_rate": win_rates[name],
            }

        dominant_name = enneagram_result.summary["ranking"][0]
        dominant_number = enneagram_types[dominant_name]["number"]
        wing_lo, wing_hi = _wing_numbers(dominant_number)
        report["enneagram"]["dominant"] = _brief(dominant_name)
        report["enneagram"]["wings"] = [
            _brief(number_to_name[wing_lo]), _brief(number_to_name[wing_hi]),
        ]
        report["enneagram"]["stress_point"] = _brief(number_to_name[_STRESS_BY_NUMBER[dominant_number]])
        report["enneagram"]["growth_point"] = _brief(number_to_name[_GROWTH_BY_NUMBER[dominant_number]])

    if instinct_result is not None:
        report["instinct"] = instinct_result.summary
        report["instinct_evidence"] = instinct_result.detail["evidence"]

    sections = []
    if disc_result is not None and strengths_result is not None:
        sections.append(integration.disc_x_strengths(disc_result, strengths_result))
    if disc_result is not None and stress_result is not None:
        sections.append(integration.stress_x_disc(disc_result, stress_result))
    if strain is not None:
        sections.append(integration.strain_x_stress(strain, stress_result))
    if motivator_result is not None:
        sections.append(integration.motivators_x_role(motivator_result, strain))
    report["integrations"] = [s for s in sections if s]

    report["plan"] = plan.build(disc_result, strengths_narrative, stress_result, strain, motivator_result)
    return report
