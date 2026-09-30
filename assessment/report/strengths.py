"""Récit des forces : chaque thème est présenté avec son coût, pas seulement son atout."""

from __future__ import annotations


def narrative(
    result, themes: dict,
    noun: str = "thème", nouns: str = "thèmes",
    bottom_note: str | None = None,
) -> dict:
    """``noun``/``nouns`` and ``bottom_note`` let a different taxonomy (e.g. the
    Ennéagramme's 9 types) reuse this same scoring narrative without inheriting
    strengths-specific wording ("thème", "une équipe ressentira votre
    absence") that wouldn't make sense outside the Forces module."""
    s = result.summary
    top, tied = s["top"], s["tied_with_fifth"]

    if tied:
        names = ", ".join(tied[:4]) + ("…" if len(tied) > 4 else "")
        plural = len(tied) != 1
        tie_note = (
            f"<b>{len(tied)} autre{'s' if plural else ''} {nouns if plural else noun} "
            f"à égalité avec le dernier de votre tête de classement</b> ({names}). À ce niveau, la "
            f"frontière de votre tête de classement est arbitraire : les {nouns} ci-dessus forment un "
            f"groupe, pas un classement strict."
        )
    else:
        tie_note = (
            "Votre tête de classement se détache nettement du reste — la frontière est réelle, pas "
            "un artefact de l'endroit où la liste a été coupée."
        )

    def card(name: str) -> dict:
        theme = themes[name]
        return {
            "name": name,
            "domain": theme["domain"],
            "colour": theme["badge_color"],
            "tagline": theme["tagline"],
            "description": theme["description"],
            "action": theme["action_tip"],
            "shadow": theme["shadow"],
            "overuse": theme["overuse"],
            "win_rate": s["win_rates"][name],
            "wins": s["wins"][name],
            "exposure": s["exposure"][name],
            "evidence": [e for e in result.detail["evidence"][name] if e["chosen"]][:4],
        }

    bottom = [
        {
            "name": name,
            "domain": themes[name]["domain"],
            "tagline": themes[name]["tagline"],
            "win_rate": s["win_rates"][name],
            "exposure": s["exposure"][name],
        }
        for name in reversed(s["bottom"])
    ]

    return {
        "tie_note": tie_note,
        "top": [card(n) for n in top],
        "supporting": [
            {"name": n, "domain": themes[n]["domain"], "tagline": themes[n]["tagline"],
             "win_rate": s["win_rates"][n]}
            for n in s["supporting"]
        ],
        "bottom": bottom,
        "bottom_note": bottom_note or (
            "Ces thèmes arrivent en dernier non pas parce que vous y êtes mauvais, mais parce que "
            "vous ne les avez pas choisis quand autre chose était proposé. Ce sont ceux que vous "
            "mettez systématiquement de côté — exactement là où une équipe ressentira votre absence."
        ),
        "domains": s["domain_percentages"],
    }
