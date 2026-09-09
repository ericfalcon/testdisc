"""Three experiments for the coming week, derived from this profile rather than
from generic advice. Each one is small enough to actually run and specific
enough to be wrong."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES

BLIND_SPOT_EXPERIMENT = {
    "D": ("Assumez seul une décision",
          "Choisissez cette semaine une décision qui vous revient vraiment et prenez-la sans chercher l'accord des autres au préalable. "
          "Annoncez-la ensuite avec votre raisonnement. Observez si le désaccord que vous cherchiez à éviter survient réellement."),
    "I": ("Envoyez un point d'étape non sollicité",
          "Choisissez une personne qui ne verrait pas autrement votre travail en cours et envoyez-lui un court point d'avancement. "
          "Vous testez si la visibilité vous coûte quelque chose, ou si ce n'est qu'une impression."),
    "S": ("Prévenez avant le prochain changement",
          "Avant votre prochain changement de plan, prévenez un jour à l'avance les deux personnes les plus concernées et demandez-leur ce que cela bouleverse pour elles. "
          "Le changement est rarement le problème ; le manque de préavis, si."),
    "C": ("Décidez une fois sans vérifier",
          "Prenez une décision que vous auriez normalement recherchée en détail, et prenez-la avec ce que vous savez déjà. Notez ce que "
          "vous auriez vérifié. En fin de semaine, regardez si cela aurait changé la réponse."),
}

STRESS_EXPERIMENT = {
    "push": ("Mettez un jour entre la pression et l'action",
             "La prochaine fois que la charge grimpe, attendez une journée complète avant d'agir sur le premier plan qui vous vient. Gardez ce plan ; "
             "comparez-le avec celui que vous avez un jour plus tard."),
    "perform": ("Dites la vérité, même si elle n'est pas flatteuse",
                "Lors de votre prochaine réunion tendue, dites une chose exacte plutôt que rassurante. Observez si le groupe "
                "le prend mieux que vous ne le pensiez."),
    "accommodate": ("Dites non une fois, sur le moment",
                    "Refusez cette semaine une chose que vous auriez normalement acceptée, et refusez-la sur le moment plutôt que d'en garder de la rancœur plus tard. "
                    "Une phrase, sans justification."),
    "retreat": ("Fixez une date de décision à voix haute",
                "La prochaine fois que vous voudrez plus de données, choisissez la date à laquelle vous déciderez sans elles et annoncez cette date à quelqu'un. "
                "C'est l'engagement qui compte."),
}


def build(disc_result, strengths_narrative, stress_result, strain, motivator_result) -> list[dict]:
    experiments: list[dict] = []

    if disc_result is not None:
        lowest = disc_result.summary["lowest"]
        title, body = BLIND_SPOT_EXPERIMENT[lowest]
        experiments.append({
            "title": title,
            "why": f"{STYLE_NAMES[lowest]} est votre dimension la plus faible.",
            "body": body,
        })

    if strengths_narrative and strengths_narrative["top"]:
        top = strengths_narrative["top"][0]
        experiments.append({
            "title": f"Repérez les excès de {top['name']}",
            "why": f"{top['name']} est votre thème dominant, et chaque thème dominant a une version qui vous coûte quelque chose.",
            "body": (
                f"{top['overuse']} Repérez une occurrence de cela cette semaine et notez ce que ça vous a coûté. "
                f"Il ne s'agit pas d'arrêter de le faire — il s'agit de le remarquer pendant que ça se produit."
            ),
        })

    if stress_result is not None:
        mode = stress_result.summary["dominant"]
        title, body = STRESS_EXPERIMENT[mode]
        experiments.append({
            "title": title,
            "why": f"Votre mode de réaction dominant sous pression est « {mode} ».",
            "body": body,
        })
    elif strain is not None and strain["band"] in ("high", "moderate"):
        largest = strain["largest"]
        experiments.append({
            "title": f"Repérez où se situe l'écart sur la dimension {STYLE_NAMES[largest]}",
            "why": f"Votre profil au travail s'écarte de {abs(strain['shifts'][largest]['delta']):.0f} points de votre profil naturel sur la dimension {STYLE_NAMES[largest]}.",
            "body": (
                "Identifiez la réunion récurrente où cet écart est le plus marqué. Changez une chose dans la façon "
                "dont vous la menez — qui parle en premier, comment elle est préparée, ou si vous devez y être."
            ),
        })
    elif motivator_result is not None:
        top = motivator_result.summary["top"][0]
        experiments.append({
            "title": f"Donnez-vous plus de {top}",
            "why": f"{top} est le moteur pour lequel vous avez le plus systématiquement fait un choix.",
            "body": (
                f"Nommez un changement concret pour la semaine prochaine qui vous donnerait mesurablement plus de {top.lower()}. "
                f"Pas un plan pour l'année — un seul changement, la semaine prochaine, que vous pouvez faire vous-même."
            ),
        })

    return experiments[:3]
