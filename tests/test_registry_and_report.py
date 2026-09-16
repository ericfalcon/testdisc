from __future__ import annotations

import random

from assessment.registry import ADDON_MODULES, CORE_MODULES, REGISTRY
from assessment.report.build import build_report

# This French edition keeps DISC (core) plus four addons — the work style
# variant, the pressure-mode module, the motivators module, and a "Forces"
# module built on an original 12-theme taxonomy rather than Gallup's
# trademarked 34-theme CliftonStrengths (see assessment/registry.py).


def _run(module_ids, seed=6):
    """Answer every item of the given modules and score them."""
    rng = random.Random(seed)
    context, results, sources, answers = {}, {}, {}, {}
    for module_id in module_ids:
        module = REGISTRY[module_id]
        items = module.build(random.Random(seed), module.variants[0], context)
        given = {
            item.uid: (rng.randint(1, 5) if item.kind == "likert5"
                       else rng.choice(["option_a", "option_b"]))
            for item in items
        }
        results[module_id] = module.score(items, given, context)
        sources[module_id] = [i.source for i in items]
        answers[module_id] = {i.source_id: given[i.uid] for i in items}
        if module_id == "disc_natural":
            context["disc_natural_item_ids"] = [i.source_id for i in items]
    return results, sources, answers


def test_every_module_builds_scores_and_round_trips():
    for module_id, module in REGISTRY.items():
        for variant in module.variants:
            items = module.build(random.Random(1), variant, {})
            assert items, f"{module_id}/{variant} built no items"
            ids = [i.source_id for i in items]
            rebuilt = module.rebuild(ids, variant)
            assert [i.source_id for i in rebuilt] == ids
            assert all(i.module_id == module_id for i in rebuilt)


def test_disc_plus_four_addons_are_registered():
    """This French edition activates DISC plus four addons, including the
    original "Forces" taxonomy — no Gallup theme or domain names anywhere."""
    assert CORE_MODULES == ("disc_natural",)
    assert set(ADDON_MODULES) == {"disc_adaptive", "stress_profile", "motivators", "strengths_core"}
    assert set(REGISTRY) == {
        "disc_natural", "disc_adaptive", "stress_profile", "motivators", "strengths_core",
    }


def test_report_builds_for_the_core_alone():
    results, sources, answers = _run(CORE_MODULES)
    report = build_report(results, sources, answers)
    assert "disc" in report
    assert report["plan"]
    assert "strain" not in report
    assert report["integrations"] == []


def test_report_builds_with_all_active_modules_together():
    """disc_adaptive depends on disc_natural for its item ids, so it must be
    built after it — _run() builds modules in the order given, and disc_natural
    is listed first here for exactly that reason."""
    module_ids = ["disc_natural", "disc_adaptive", "stress_profile", "motivators", "strengths_core"]
    results, sources, answers = _run(module_ids)
    report = build_report(results, sources, answers)
    assert "disc" in report
    assert "strain" in report
    assert "stress" in report
    assert "motivators" in report
    assert "strengths" in report
    assert report["plan"]
    assert report["integrations"], "at least one cross-module section should fire"


def test_built_items_are_tagged_with_their_own_module():
    """The runner looks the module up by the item's module_id; a mismatch breaks
    the questionnaire even though scoring still works."""
    for module_id, module in REGISTRY.items():
        for variant in module.variants:
            items = module.build(random.Random(1), variant, {})
            assert {i.module_id for i in items} == {module_id}
            assert all(i.uid.startswith(f"{module_id}:") for i in items)


def test_pdf_builds_for_the_disc_module():
    from app.pdf import build_pdf

    results, sources, answers = _run(["disc_natural"])
    report = build_report(results, sources, answers)
    data = build_pdf(report, results).getvalue()
    assert data.startswith(b"%PDF"), "produced no PDF"
    assert data.rstrip().endswith(b"%%EOF"), "produced a truncated PDF"
    assert data.count(b"/Type /Page") >= 1, "produced no pages"


def test_pdf_builds_with_identity_too():
    """identity is optional (backward-compatible with the call above), but
    must not break the build when a name and session are supplied — that's
    the whole point of passing it through."""
    from app.pdf import build_pdf

    results, sources, answers = _run(["disc_natural"])
    report = build_report(results, sources, answers)
    identity = {"prenom": "Ada", "nom": "Lovelace", "session": "Gestion du temps — 12 novembre"}
    data = build_pdf(report, results, identity).getvalue()
    assert data.startswith(b"%PDF"), "produced no PDF"
    assert data.rstrip().endswith(b"%%EOF"), "produced a truncated PDF"
