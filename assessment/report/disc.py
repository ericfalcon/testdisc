"""DISC narrative, written to respect the confidence in the numbers."""

from __future__ import annotations

from ..scoring.disc import STYLE_NAMES

PRIMARY = {
    "D": "Votre mode de fonctionnement de base est proactif et déterminé. Vous puisez votre énergie dans le fait de lever des obstacles, de prendre des initiatives et d'aller vers un résultat concret, et vous voulez pouvoir décider sans attendre d'autorisation.",
    "I": "Votre mode de fonctionnement de base est expressif et relationnel. Vous réfléchissez à voix haute, vous créez de la dynamique par le contact humain, et vous donnez le meilleur de vous-même là où il y a du dialogue, de l'enthousiasme visible et un mérite partagé.",
    "S": "Votre mode de fonctionnement de base est patient et fiable. Vous construisez une confiance qui dure, vous tenez un rythme stable sur la durée, et vous êtes la personne sur laquelle les autres bâtissent leurs plans.",
    "C": "Votre mode de fonctionnement de base est analytique et exigeant. Vous décomposez les problèmes, vous voulez des décisions fondées sur quelque chose de vérifiable, et vous tirez une vraie satisfaction d'un travail qui résiste à l'examen.",
}

BLEND = {
    "D-I": "Votre Influence ajoute de la persuasion à votre détermination : vous entraînez les autres avec vous plutôt que de simplement les pousser.",
    "D-S": "Votre Stabilité tempère votre détermination par de la patience, si bien que l'élan arrive sans laisser personne de côté.",
    "D-C": "Votre Conformité rend votre détermination précise : vous voulez à la fois la vitesse <i>et</i> une réponse défendable.",
    "I-D": "Votre Dominance transforme l'enthousiasme en résultats concrets — vous passez de l'idée à l'action plus vite que la plupart des gens.",
    "I-S": "Votre Stabilité donne de la profondeur à votre chaleur humaine : les autres vous perçoivent comme sincèrement intéressé, pas seulement sociable.",
    "I-C": "Votre Conformité ancre votre enthousiasme, si bien que ce que vous proposez résiste généralement à l'épreuve du détail.",
    "S-D": "Votre Dominance donne de la fermeté à votre patience : quand c'est important, vous savez tenir votre position.",
    "S-I": "Votre Influence rend votre Stabilité sociable — vous êtes la personne qui maintient le lien dans un groupe.",
    "S-C": "Votre Conformité rend votre fiabilité rigoureuse : ce que vous prenez en charge n'est jamais laissé de côté.",
    "C-D": "Votre Dominance transforme l'analyse en argumentaire : vous ne vous contentez pas de trouver la faille, vous poussez pour qu'elle soit corrigée.",
    "C-I": "Votre Influence vous permet de traduire l'analyse pour ceux qui ne la liront jamais.",
    "C-S": "Votre Stabilité rend votre rigueur tenable dans la durée — minutieuse, et toujours là au neuvième mois.",
}

BLIND_SPOT = {
    "D": "La Dominance est votre dimension la plus faible. Vous cherchez l'accord avant d'agir, ce qui paraît collaboratif jusqu'au moment où une décision a besoin d'un responsable et que personne ne s'en empare. Le coût retombe sur celui qui finit par le faire.",
    "I": "L'Influence est votre dimension la plus faible. Vous laissez le travail parler de lui-même, ce qui est honorable mais peu fiable : les personnes qui n'ont jamais de vos nouvelles se forgent une opinion de votre travail à partir du récit de quelqu'un d'autre.",
    "S": "La Stabilité est votre dimension la plus faible. Vous passez vite à autre chose, alors que les personnes qui avaient besoin que le plan précédent tienne continuent de s'y référer. Le changement est rarement le problème ; le manque de préavis, si.",
    "C": "La Conformité est votre dimension la plus faible. Vous agissez sur l'essentiel, ce qui est rapide et parfois coûteux. Le détail que vous avez sauté a tendance à réapparaître sous la forme de l'urgence de quelqu'un d'autre.",
}

# Écrit délibérément du point de vue de l'autre personne. Le sujet est ce que
# vous êtes à travailler avec, pas ce que vous avez l'intention de faire.
FRICTION = {
    "D": [
        ("à dominante Stabilité", "Les décisions arrivent déjà prises et on attend d'eux qu'ils absorbent le changement. Ce qui aide : expliquer le raisonnement, et prévenir un jour à l'avance avant que ce soit définitif."),
        ("à dominante Conformité", "Votre rapidité donne l'impression que vous n'avez pas vérifié. Ce qui aide : dire ce que vous avez effectivement vérifié, et ce que vous avez choisi de ne pas vérifier."),
    ],
    "I": [
        ("à dominante Conformité", "Votre énergie donne l'impression d'une affirmation qui n'a pas encore été prouvée. Ce qui aide : mettre les détails par écrit avant de présenter votre idée."),
        ("à dominante Dominance", "La discussion ressemble à un retard alors qu'ils voulaient une décision. Ce qui aide : commencer par la recommandation, puis expliquer le raisonnement."),
    ],
    "S": [
        ("à dominante Dominance", "Votre prudence donne l'impression d'une résistance. Ce qui aide : nommer ce dont vous avez besoin pour avancer, plutôt que ce qui vous inquiète."),
        ("à dominante Influence", "Votre discrétion donne l'impression de désapprobation. Ce qui aide : exprimer à voix haute ce qui est positif ; ils ne peuvent pas le deviner."),
    ],
    "C": [
        ("à dominante Influence", "Vos questions sont perçues comme un scepticisme envers eux personnellement. Ce qui aide : séparer la remise en question de l'affirmation de votre opinion sur la personne."),
        ("à dominante Dominance", "Votre minutie donne l'impression d'une réticence à s'engager. Ce qui aide : donner une réponse provisoire en précisant votre degré de confiance."),
    ],
}

ENVIRONMENT = {
    "D": "Un environnement qui va vite et qui récompense le mérite, avec une réelle autonomie, des indicateurs visibles, et peu de distance entre une décision et sa conséquence.",
    "I": "Un environnement collaboratif et expressif, où les idées sont partagées tôt, où la contribution de chacun est reconnue à voix haute, et où le travail se fait avec les autres plutôt qu'à côté d'eux.",
    "S": "Un environnement stable et prévenant, avec des attentes prévisibles, un préavis suffisant avant tout changement, et des collègues qui restent assez longtemps pour construire une relation de confiance.",
    "C": "Un environnement structuré et rigoureux, avec accès à une information fiable, le temps de bien faire le travail, et le respect du travail soigné.",
}

HEDGES = {
    "High": ("Vos réponses étaient cohérentes entre elles, le profil ci-dessous peut donc être lu tel quel.", ""),
    "Moderate": ("Vos réponses étaient globalement cohérentes. Considérez la tendance générale comme fiable et les chiffres exacts comme approximatifs.", "dans l'ensemble, "),
    "Low": ("Vos réponses n'étaient pas assez cohérentes entre elles pour établir un profil fiable. Ce qui suit en est la meilleure lecture possible, mais chaque affirmation ci-dessous est à vérifier plutôt qu'à prendre comme un fait établi.", "sur la base de ces réponses, et avec prudence, "),
}


def narrative(result, confidence: dict, descriptions: dict) -> dict:
    s = result.summary
    norm, se = s["normalized"], s["standard_error"]
    primary, secondary, lowest = s["primary"], s["secondary"], s["lowest"]
    level = confidence["level"]
    caveat, hedge = HEDGES[level]

    style_info = descriptions["single"].get(s["style_code"], descriptions.get("balanced", {}))

    sep = result.detail["primary_vs_secondary"]
    if sep["separated"]:
        order_claim = (
            f"{STYLE_NAMES[primary]} est {hedge}votre dimension dominante à "
            f"<b>{norm[primary]:.0f} ± {se[primary]:.0f}</b>, nettement devant "
            f"{STYLE_NAMES[secondary]} à <b>{norm[secondary]:.0f} ± {se[secondary]:.0f}</b>."
        )
    else:
        order_claim = (
            f"{STYLE_NAMES[primary]} ({norm[primary]:.0f} ± {se[primary]:.0f}) et "
            f"{STYLE_NAMES[secondary]} ({norm[secondary]:.0f} ± {se[secondary]:.0f}) sont "
            f"<b>trop proches pour être départagées</b> avec ce nombre de questions — l'écart de "
            f"{sep['difference']:.0f} points reste dans la marge d'erreur de mesure. Lisez-les comme "
            f"un mélange plutôt qu'un classement ; aucune des deux n'est votre style « réel »."
        )

    claims = [
        {
            "title": "Comment vous fonctionnez",
            "text": PRIMARY[primary],
            "evidence": result.detail["evidence"][primary],
        },
        {
            "title": "Le mélange",
            "text": BLEND.get(f"{primary}-{secondary}", "Vos deux dimensions dominantes se combinent en un style véritablement mixte."),
            "evidence": result.detail["evidence"][secondary],
        },
        {
            "title": "Votre angle mort",
            "text": BLIND_SPOT[lowest],
            "evidence": result.detail["evidence"][lowest],
        },
    ]

    pace_word = "rapide et proactif" if s["pace"] >= 0 else "réfléchi et posé"
    focus_word = "les personnes et les relations" if s["focus"] >= 0 else "les tâches et la logique"

    return {
        "confidence_caveat": caveat,
        "order_claim": order_claim,
        "separated": sep["separated"],
        "title": style_info.get("title", "Votre profil DISC"),
        "headline": style_info.get("headline", ""),
        "claims": claims,
        "tempo": (
            f"Votre rythme se lit comme <b>{pace_word}</b> (rythme {s['pace']:+.0f}), avec une attention portée sur "
            f"<b>{focus_word}</b> (focus {s['focus']:+.0f}). Intensité du style : <b>{s['intensity'].lower()}</b>."
        ),
        "environment": ENVIRONMENT[primary],
        "friction": FRICTION[primary],
        "strengths": style_info.get("strengths", ""),
        "challenges": style_info.get("challenges", ""),
        "communication": style_info.get("communication_tips", ""),
        "motivators": style_info.get("motivators", ""),
        "stress_triggers": style_info.get("stress_triggers", ""),
        "under_pressure": style_info.get("under_pressure", ""),
        "time_relationship": style_info.get("time_relationship", ""),
    }
