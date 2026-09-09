"""Build docs/guide-formateur-profils-disc.md from data/disc_descriptions.json.

The 13 profiles (4 single styles, 8 blends, 1 balanced) live in one JSON file
and are used to build the trainee's own report. This script turns the same
data into a standalone reference document for the trainer — a one-page-per-
style cheat sheet to have on hand before a session, without needing to run
the test themselves.

Run it after editing data/disc_descriptions.json to keep the guide in sync:

    python3 scripts/build_trainer_guide.py

tests/test_trainer_guide.py fails if the checked-in file drifts from what
this script would produce, so a description edit without a re-run is caught.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "disc_descriptions.json"
OUTPUT_PATH = ROOT / "docs" / "guide-formateur-profils-disc.md"

ORDER = ["D", "I", "S", "C", "DI", "ID", "IS", "SI", "SC", "CS", "CD", "DC"]


def _section(profile: dict) -> list[str]:
    return [
        f"## {profile['title']}",
        "",
        f"*{profile['headline']}*",
        "",
        profile["description"],
        "",
        f"**Forces.** {profile['strengths']}",
        "",
        f"**Axes de progrès.** {profile['challenges']}",
        "",
        f"**Rapport au temps.** {profile['time_relationship']}",
        "",
        f"**Prise de décision.** {profile['decision_making']}",
        "",
        f"**Rapport aux interruptions.** {profile['interruptions']}",
        "",
        f"**Comment communiquer avec cette personne.** {profile['communication_tips']}",
        "",
    ]


def build(data: dict) -> str:
    lines = [
        "# Guide formateur — les 13 profils DISC",
        "",
        "Référence rapide pour préparer une session : les 13 profils que peut renvoyer "
        "l'application (4 styles simples, 8 combinaisons des deux dimensions dominantes, "
        "et un profil équilibré), avec pour chacun l'essentiel à retenir. Ce document est "
        "fait pour le formateur — les stagiaires reçoivent leur propre profil, plus détaillé, "
        "en PDF à la fin du test.",
        "",
        "Pour chaque profil : l'accroche, la description, les forces, les axes de progrès, et "
        "quatre points utiles pour une formation à la gestion du temps — le rapport au temps, la "
        "prise de décision, le rapport aux interruptions, et comment communiquer avec cette personne.",
        "",
    ]
    for code in ORDER:
        lines += _section(data["single"][code])
        lines.append("---")
        lines.append("")
    lines += _section(data["balanced"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(build(data), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
