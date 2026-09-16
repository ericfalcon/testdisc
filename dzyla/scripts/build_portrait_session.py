"""Build docs/portrait-session-formateur.html from data/disc_descriptions.json.

"Portrait de session" is the standalone, offline HTML tool a trainer opens to
analyse the CSV exported from the Google Sheet: it groups a session's
stagiaires by DISC style and shows each one's full fiche, using the exact
same source text as the trainee's own report and the trainer guide (see
build_trainer_guide.py). This script injects that text into the tool's
template so all three stay in sync automatically.

Run it after editing data/disc_descriptions.json to keep the tool in sync:

    python3 scripts/build_portrait_session.py

tests/test_portrait_session_tool.py fails if the checked-in file drifts from
what this script would produce, so a description edit without a re-run is
caught — the same guarantee build_trainer_guide.py gives its own output.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "disc_descriptions.json"
TEMPLATE_PATH = ROOT / "docs" / "portrait-session-formateur.template.html"
OUTPUT_PATH = ROOT / "docs" / "portrait-session-formateur.html"

PLACEHOLDER = "__PROFILES_JSON__"

# The tool only ever needs the fields it actually renders (see FIELD_LABELS in
# the template plus the header line built from title/headline/description).
FIELDS = (
    "title",
    "headline",
    "description",
    "strengths",
    "challenges",
    "time_relationship",
    "decision_making",
    "interruptions",
    "communication_tips",
)


def build_profiles(data: dict) -> dict:
    profiles: dict[str, dict] = {}
    for code, profile in data["single"].items():
        profiles[code] = {field: profile[field] for field in FIELDS}
    profiles["balanced"] = {field: data["balanced"][field] for field in FIELDS}
    return profiles


def build(data: dict, template: str) -> str:
    profiles_json = json.dumps(build_profiles(data), ensure_ascii=False, indent=2)
    if PLACEHOLDER not in template:
        raise ValueError(f"template is missing the {PLACEHOLDER} placeholder")
    return template.replace(PLACEHOLDER, profiles_json)


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    OUTPUT_PATH.write_text(build(data, template), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
