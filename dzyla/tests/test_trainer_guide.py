"""The trainer's reference guide (docs/guide-formateur-profils-disc.md) is
generated from data/disc_descriptions.json by scripts/build_trainer_guide.py.
This test fails if someone edits the profile descriptions without re-running
that script, so the checked-in guide can't silently drift from what the app
actually shows trainees.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_trainer_guide as guide  # noqa: E402


def test_guide_matches_the_current_descriptions():
    data = json.loads(guide.DATA_PATH.read_text(encoding="utf-8"))
    expected = guide.build(data)
    actual = guide.OUTPUT_PATH.read_text(encoding="utf-8")
    assert actual == expected, (
        "docs/guide-formateur-profils-disc.md is out of date — run "
        "`python3 scripts/build_trainer_guide.py` after editing "
        "data/disc_descriptions.json"
    )


def test_guide_covers_all_thirteen_profiles():
    data = json.loads(guide.DATA_PATH.read_text(encoding="utf-8"))
    text = guide.OUTPUT_PATH.read_text(encoding="utf-8")
    for code in guide.ORDER:
        assert data["single"][code]["title"] in text
    assert data["balanced"]["title"] in text
