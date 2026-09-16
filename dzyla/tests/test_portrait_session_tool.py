"""The trainer's session-analysis tool (docs/portrait-session-formateur.html)
embeds the same profile text as the trainee's report and the trainer guide,
injected into docs/portrait-session-formateur.template.html by
scripts/build_portrait_session.py. This test fails if someone edits the
profile descriptions, or the template, without re-running that script, so
the checked-in tool can't silently drift from what the app actually shows
trainees.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_portrait_session as tool  # noqa: E402

ALL_CODES = [
    "D", "I", "S", "C", "DI", "ID", "IS", "SI", "SC", "CS", "CD", "DC", "balanced",
]


def test_tool_matches_the_current_descriptions_and_template():
    data = json.loads(tool.DATA_PATH.read_text(encoding="utf-8"))
    template = tool.TEMPLATE_PATH.read_text(encoding="utf-8")
    expected = tool.build(data, template)
    actual = tool.OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/portrait-session-formateur.html is out of date — run "
        "`python3 scripts/build_portrait_session.py` after editing "
        "data/disc_descriptions.json or the template"
    )


def test_tool_embeds_all_thirteen_profiles_with_the_expected_fields():
    data = json.loads(tool.DATA_PATH.read_text(encoding="utf-8"))
    profiles = tool.build_profiles(data)
    assert set(profiles) == set(ALL_CODES)
    for code in ALL_CODES:
        for field in tool.FIELDS:
            assert profiles[code][field], f"{code}.{field} is empty"


def test_output_has_no_leftover_placeholder_and_is_a_full_html_document():
    text = tool.OUTPUT_PATH.read_text(encoding="utf-8")
    assert tool.PLACEHOLDER not in text
    assert "<!doctype html>" in text.lower() or "<!DOCTYPE html>" in text
    assert "Portrait de session" in text
