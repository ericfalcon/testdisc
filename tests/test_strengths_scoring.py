"""The property that matters: a theme's rank must not depend on how often the
item pool happened to offer it."""

from __future__ import annotations

import random

from assessment import items as pools
from assessment.scoring import strengths


def _themes(*names):
    return {
        name: {
            "name": name, "domain": "Executing", "badge_color": "#000000",
            "tagline": "t", "description": "d", "action_tip": "a",
            "shadow": "s", "overuse": "o",
        }
        for name in names
    }


def _item(item_id, a_tags, b_tags):
    return {
        "id": item_id, "question": "q", "option_a": "A", "option_b": "B",
        "alignment": {"option_a": list(a_tags), "option_b": list(b_tags)},
    }


def test_win_rate_is_independent_of_exposure():
    """Rare and common themes chosen at the same rate must score the same.

    Counting raw wins gave the common theme four times the score for identical
    behaviour, which is what made the old top five partly a property of the pool.
    """
    themes = _themes("Rare", "Common", "Filler")
    items, answers = [], {}
    # Rare is offered twice and chosen once; Common is offered eight times and
    # chosen four. Identical behaviour, four times the exposure.
    items.append(_item("r1", ["Rare"], ["Filler"]))
    answers["r1"] = "option_a"
    items.append(_item("r2", ["Rare"], ["Filler"]))
    answers["r2"] = "option_b"
    for index in range(4):
        items.append(_item(f"c{index}a", ["Common"], ["Filler"]))
        answers[f"c{index}a"] = "option_a"
        items.append(_item(f"c{index}b", ["Common"], ["Filler"]))
        answers[f"c{index}b"] = "option_b"

    summary = strengths.score(items, answers, themes).summary
    assert summary["win_rates"]["Rare"] == summary["win_rates"]["Common"] == 0.5
    assert summary["wins"]["Common"] > summary["wins"]["Rare"]
    assert summary["exposure"]["Common"] > summary["exposure"]["Rare"]


def test_doubling_exposure_at_the_same_ratio_does_not_change_the_ranking():
    themes = _themes("Alpha", "Beta")
    small_items = [_item("s1", ["Alpha"], ["Beta"]), _item("s2", ["Alpha"], ["Beta"])]
    small_answers = {"s1": "option_a", "s2": "option_a"}
    big_items = small_items + [_item("s3", ["Alpha"], ["Beta"]), _item("s4", ["Alpha"], ["Beta"])]
    big_answers = dict(small_answers, s3="option_a", s4="option_a")

    small = strengths.score(small_items, small_answers, themes).summary
    big = strengths.score(big_items, big_answers, themes).summary
    assert small["ranking"] == big["ranking"]
    assert small["win_rates"] == big["win_rates"]


def test_an_option_with_several_tags_does_not_inflate_one_choice():
    """One click awarded one, two or three points before, depending on tagging."""
    themes = _themes("One", "Two", "Three", "Other")
    items = [_item("m1", ["One", "Two", "Three"], ["Other"])]
    summary = strengths.score(items, {"m1": "option_a"}, themes).summary
    assert summary["win_rates"]["One"] == summary["win_rates"]["Two"] == summary["win_rates"]["Three"] == 1.0
    assert summary["exposure"]["One"] == 1


def test_themes_level_with_the_fifth_are_reported_as_tied():
    themes = _themes(*[f"T{i}" for i in range(8)])
    items, answers = [], {}
    for index in range(8):
        items.append(_item(f"i{index}", [f"T{index}"], [f"T{(index + 1) % 8}"]))
        answers[f"i{index}"] = "option_a"
    summary = strengths.score(items, answers, themes).summary
    assert summary["tied_with_fifth"], "identical win rates must be reported as a tie"


def test_unanswered_items_do_not_count_as_exposure():
    themes = _themes("Alpha", "Beta")
    items = [_item("a", ["Alpha"], ["Beta"]), _item("b", ["Alpha"], ["Beta"])]
    summary = strengths.score(items, {"a": "option_a"}, themes).summary
    assert summary["exposure"]["Alpha"] == 1


def test_graduated_answers_award_partial_credit():
    """The scale between the two statements ("lean_a", "neutral", "lean_b")
    must score as a fraction of a win, not as a full point or a zero — and the
    old all-or-nothing answers ("option_a"/"option_b") must still score
    exactly as before, since real exports predate the graduated scale."""
    themes = _themes("Alpha", "Beta")
    items = [
        _item("a", ["Alpha"], ["Beta"]),
        _item("b", ["Alpha"], ["Beta"]),
        _item("c", ["Alpha"], ["Beta"]),
        _item("d", ["Alpha"], ["Beta"]),
        _item("e", ["Alpha"], ["Beta"]),
    ]
    answers = {
        "a": "option_a", "b": "lean_a", "c": "neutral", "d": "lean_b", "e": "option_b",
    }
    summary = strengths.score(items, answers, themes).summary
    assert summary["wins"]["Alpha"] == 1.0 + 0.75 + 0.5 + 0.25 + 0.0
    assert summary["wins"]["Beta"] == 0.0 + 0.25 + 0.5 + 0.75 + 1.0
    assert summary["exposure"]["Alpha"] == summary["exposure"]["Beta"] == 5


def test_real_pool_produces_a_full_ranking():
    themes = pools.strengths_themes()
    items = pools.sample_strengths(random.Random(4), 35)
    rng = random.Random(8)
    answers = {i["id"]: rng.choice(["option_a", "option_b"]) for i in items}
    summary = strengths.score(items, answers, themes).summary
    assert len(summary["ranking"]) == len(themes)
    assert len(summary["top"]) == 5
    assert all(0.0 <= r <= 1.0 for r in summary["win_rates"].values())
