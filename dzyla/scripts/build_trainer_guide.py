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


def _intro() -> list[str]:
    return [
        "# Guide formateur — les 13 profils DISC",
        "",
        "Référence rapide pour préparer une session : les 13 profils que peut renvoyer "
        "l'application (4 styles simples, 8 combinaisons des deux dimensions dominantes, "
        "et un profil équilibré), avec pour chacun l'essentiel à retenir. Ce document est "
        "fait pour le formateur — les stagiaires reçoivent leur propre profil, plus détaillé, "
        "en PDF à la fin du test. Aucune connaissance préalable du DISC n'est nécessaire pour "
        "l'utiliser : la section qui suit résume le modèle en deux minutes.",
        "",
        "## Comprendre le DISC en deux minutes",
        "",
        "Le DISC décrit des tendances de comportement observables — pas une personnalité figée, "
        "et encore moins un diagnostic. Il croise deux questions simples : la personne réagit-elle "
        "plutôt vite et activement, ou plutôt de façon posée et réfléchie ? Et est-elle plutôt "
        "tournée vers la tâche et le résultat, ou plutôt vers les personnes et la relation ? En "
        "croisant ces deux axes, on obtient quatre dimensions :",
        "",
        "- **D — Dominance** : rapide et tourné vers la tâche. Direct, orienté résultats, aime "
        "décider et avancer.",
        "- **I — Influence** : rapide et tourné vers la relation. Expressif, sociable, aime "
        "convaincre et fédérer.",
        "- **S — Stabilité** : posé et tourné vers la relation. Patient, coopératif, aime la "
        "constance et la confiance durable.",
        "- **C — Conformité** : posé et tourné vers la tâche. Méthodique, rigoureux, aime la "
        "précision et la vérification.",
        "",
        "Tout le monde a un peu des quatre dimensions, mais dans des proportions qui varient d'une "
        "personne à l'autre. Le test retient les deux dimensions les plus fortes de chaque "
        "stagiaire : sa dimension **dominante** (celle qui le décrit le mieux) et sa dimension "
        "**secondaire** (qui la nuance). C'est ce qui donne les 13 profils de ce guide : les 4 "
        "styles « purs » quand la dominante dépasse nettement la secondaire (D, I, S, C), les 8 "
        "combinaisons quand les deux se mélangent de façon plus équilibrée — l'ordre des lettres "
        "compte, DI (dominante D, nuancée par I) se lit différemment de ID (dominante I, nuancée "
        "par D) — et un profil « équilibré » quand aucune des quatre dimensions ne se détache "
        "vraiment.",
        "",
        "Deux autres indications accompagnent le profil dans le rapport remis au stagiaire :",
        "",
        "- **L'intensité** (situationnelle / modérée / marquée) dit à quel point le style se "
        "manifeste de façon constante, ou seulement selon le contexte.",
        "- **La confiance** (élevée / modérée / faible) dit si les réponses du stagiaire étaient "
        "cohérentes entre elles. Une confiance faible signifie que le profil est une hypothèse à "
        "vérifier avec la personne, pas un fait établi.",
        "",
        "Aucune dimension n'est meilleure qu'une autre : chacune a ses forces et son coût selon le "
        "contexte. L'intérêt de ce guide n'est pas de mettre un stagiaire dans une case, mais "
        "d'anticiper comment il aborde probablement son temps, ses priorités et ses décisions, "
        "pour adapter vos exemples et vos conseils pendant la session.",
        "",
        "Pour chaque profil : l'accroche, la description, les forces, les axes de progrès, et "
        "quatre points utiles pour une formation à la gestion du temps — le rapport au temps, la "
        "prise de décision, le rapport aux interruptions, et comment communiquer avec cette "
        "personne.",
        "",
        "**Un mot sur le « vous ».** Chaque fiche reprend telles quelles les phrases du rapport "
        "remis au stagiaire, qui s'adresse directement à lui — c'est pour cela qu'elles sont "
        "écrites à la deuxième personne (« vous êtes... », « vous décidez... »). En lisant une "
        "fiche, remplacez mentalement « vous » par « le stagiaire de ce profil » : ce n'est pas le "
        "formateur qui est visé, c'est la personne que ce profil décrit.",
        "",
    ]


def build(data: dict) -> str:
    lines = _intro()
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
