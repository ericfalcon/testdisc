"""The report. Every claim is followed by the answers that produced it."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime

import streamlit as st

from assessment.registry import ADDON_MODULES, REGISTRY
from assessment.report.build import build_report
from assessment.scoring.disc import STRAIN_BAND_LABELS, STYLE_NAMES
from assessment.scoring.motivators import DRIVER_BLURBS
from assessment.scoring.stress import MODE_BLURBS, MODE_LABELS
from assessment.types import LIKERT_OPTIONS

from . import components as ui
from . import plots, sheet_sync, state
from .pdf import build_pdf


LEVEL_LABELS_FR = {"High": "élevée", "Moderate": "modérée", "Low": "faible"}


def _likert_evidence(entries: list[dict]) -> None:
    for entry in entries:
        answer = LIKERT_OPTIONS[entry["response"] - 1]
        flag = " · formulation inversée" if entry.get("reverse") else ""
        st.markdown(
            f'<div style="margin-bottom:9px;">'
            f'<span class="chan">{html.escape(entry["id"])}{flag}</span><br>'
            f'<span style="font-size:0.94rem;">“{html.escape(entry["question"])}”</span><br>'
            f'<span class="num" style="color:{ui.SIGNAL};font-size:0.88rem;">→ {html.escape(answer)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )


def _choice_evidence(entries: list[dict], key: str = "text") -> None:
    for entry in entries:
        st.markdown(
            f'<div style="margin-bottom:9px;">'
            f'<span class="chan">{html.escape(entry["id"])}</span><br>'
            f'<span class="num" style="color:{ui.SIGNAL};font-size:0.88rem;">vous avez choisi →</span> '
            f'<span style="font-size:0.94rem;">{html.escape(entry[key])}</span></div>',
            unsafe_allow_html=True,
        )


def _confidence_banner(report: dict) -> None:
    low = {m: c for m, c in report["confidence"].items() if c["level"] == "Low"}
    if not low:
        return
    names = ", ".join(REGISTRY[m].title for m in low)
    reasons = sorted({r for c in low.values() for r in c["reasons"]})
    ui.caveat(
        f"Confiance faible : {names}",
        "Le profil de réponses ne permet pas une lecture fiable. Considérez ce qui suit comme des "
        "questions à vérifier au regard de votre propre expérience, pas comme des conclusions établies.",
        reasons,
    )


def _disc_section(report: dict) -> None:
    disc = report["disc"]
    summary = st.session_state.results["disc_natural"].summary
    confidence = report["confidence"].get("disc_natural", {"level": "Moderate"})

    st.markdown(f"## {html.escape(disc['title'])}")
    st.markdown(
        f'<p style="color:{ui.SLATE};margin-top:-0.4rem;">{html.escape(disc["headline"])}</p>',
        unsafe_allow_html=True,
    )
    level = confidence["level"]
    st.markdown(
        f'<span class="tag" style="color:{ui.CONFIDENCE_COLOURS[level]};">confiance · {LEVEL_LABELS_FR.get(level, level)}</span>'
        f'<span class="tag">intensité · {summary["intensity"]}</span>'
        f'<span class="tag">style · {summary["style_code"]}</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    left, right = st.columns([1, 1])
    with left:
        st.pyplot(
            plots.circumplex(summary["normalized"], report.get("adaptive", {}).get("normalized")),
            use_container_width=True,
        )
        st.caption(
            "Comment lire ce point. Sa **direction** indique le mélange de vos deux dimensions "
            "les plus fortes (par exemple entre Influence et Dominance). Sa **distance au centre** "
            "indique l'intensité du profil : proche du centre, votre profil est plus situationnel "
            "et varie selon le contexte ; loin du centre, il est marqué et se manifeste de façon "
            "plus constante. Les anneaux (situationnelle / modérée / marquée) sont les mêmes seuils "
            "que ceux utilisés dans le texte du rapport."
        )
    with right:
        st.markdown('<div class="chan">Scores par dimension · ± une erreur-type</div>',
                    unsafe_allow_html=True)
        st.write("")
        bars = "".join(
            ui.errorbar(f"{style} · {STYLE_NAMES[style]}", summary["normalized"][style],
                        summary["standard_error"][style], ui.STYLE_COLOURS[style])
            for style in "DISC"
        )
        st.markdown(bars, unsafe_allow_html=True)

    st.markdown(f'<div class="panel"><p>{disc["order_claim"]}</p>'
                f'<p style="color:{ui.SLATE};font-size:0.93rem;margin-bottom:0;">'
                f'{html.escape(disc["confidence_caveat"])}</p></div>', unsafe_allow_html=True)

    for claim in disc["claims"]:
        ui.panel(claim["title"], f'<p>{claim["text"]}</p>')
        with st.expander(f"Pourquoi ? — les réponses derrière « {claim['title']} »"):
            _likert_evidence(claim["evidence"])

    ui.panel("Rythme et attention", f'<p>{disc["tempo"]}</p>')
    if disc.get("time_relationship"):
        ui.panel("Votre rapport au temps", f'<p>{html.escape(disc["time_relationship"])}</p>')
    if disc.get("decision_making"):
        ui.panel("Votre prise de décision", f'<p>{html.escape(disc["decision_making"])}</p>')
    if disc.get("interruptions"):
        ui.panel("Votre rapport aux interruptions", f'<p>{html.escape(disc["interruptions"])}</p>')
    ui.panel("Où vous êtes le plus efficace", f'<p>{html.escape(disc["environment"])}</p>')

    friction = "".join(
        f'<p><b>Pour un collègue {html.escape(who)}.</b> {html.escape(text)}</p>'
        for who, text in disc["friction"]
    )
    ui.panel("Avec qui il vous est le plus difficile de travailler", friction)

    detail_html = "".join(
        f"<p><b>{html.escape(label)}.</b> {html.escape(disc[key])}</p>"
        for label, key in [
            ("Forces naturelles", "strengths"),
            ("Axes de progrès", "challenges"),
            ("Comment communiquer avec vous", "communication"),
            ("Ce qui vous motive", "motivators"),
            ("Ce qui déclenche du stress", "stress_triggers"),
            ("Sous pression", "under_pressure"),
        ]
        if disc.get(key)
    )
    if detail_html:
        ui.panel("Détail du style — forces, difficultés, communication, pression", detail_html)


def _strain_section(report: dict) -> None:
    strain = report["strain"]
    st.markdown("## Le naturel face au travail")
    st.markdown(
        f'<span class="tag">indice de tension · <span class="num">{strain["index"]:.0f}</span></span>'
        f'<span class="tag">charge d\'adaptation {STRAIN_BAND_LABELS.get(strain["band"], strain["band"])}</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    rows = []
    for style in "DISC":
        shift = strain["shifts"][style]
        marker = "écart réel" if shift["significant"] else "dans la marge de bruit"
        rows.append(
            f'<p><b>{STYLE_NAMES[style]}</b> '
            f'<span class="num">{shift["natural"]:.0f} → {shift["adaptive"]:.0f} '
            f'({shift["delta"]:+.0f})</span> '
            f'<span class="chan">· {marker}</span></p>'
        )
    ui.panel("Ce que le poste vous demande", "".join(rows))
    st.caption(
        "Un écart marqué *dans la marge de bruit* est plus petit que l'erreur de mesure et ne doit "
        "pas être lu comme une différence réelle."
    )


def _strengths_section(report: dict) -> None:
    strengths = report["strengths"]
    st.markdown("## Vos forces naturelles")
    st.markdown(f'<div class="panel"><p>{strengths["tie_note"]}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="chan">Équilibre entre domaines</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown(
        "".join(
            ui.errorbar(domain, pct, 0, ui.DOMAIN_COLOURS[domain], suffix="%")
            for domain, pct in strengths["domains"].items()
        ),
        unsafe_allow_html=True,
    )
    st.write("")

    for rank, theme in enumerate(strengths["top"], start=1):
        st.markdown(
            f"""<div class="theme-card" style="border-left-color:{theme['colour']};">
              <div class="theme-rank">#{rank} · {html.escape(theme['domain'])} ·
                <span class="num">choisi {theme['wins']}/{theme['exposure']} fois proposé</span></div>
              <div class="theme-name">{html.escape(theme['name'])}</div>
              <p style="color:{ui.SLATE};margin:4px 0 8px 0;">{html.escape(theme['tagline'])}</p>
              <p style="margin:0 0 8px 0;">{html.escape(theme['description'])}</p>
              <p style="margin:0;font-size:0.94rem;"><b>À utiliser ainsi :</b> {html.escape(theme['action'])}</p>
              <div class="theme-cost">
                <b>Comment ça se voit.</b> {html.escape(theme['shadow'])}<br>
                <b>Quand ça vous coûte.</b> {html.escape(theme['overuse'])}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.expander(f"Pourquoi {theme['name']} ? — les choix derrière ce thème"):
            _choice_evidence(theme["evidence"])

    if strengths["supporting"]:
        first = len(strengths["top"]) + 1
        last = first + len(strengths["supporting"]) - 1
        label = f"Thèmes intermédiaires (#{first}–#{last})" if last > first else f"Thème intermédiaire (#{first})"
        with st.expander(label):
            for rank, theme in enumerate(strengths["supporting"], start=first):
                st.markdown(
                    f"**#{rank} {theme['name']}** *({theme['domain']})* — {theme['tagline']} "
                    f"`{theme['win_rate']:.0%}`"
                )

    ui.panel(
        "Ce que vous mettez de côté",
        f'<p>{html.escape(strengths["bottom_note"])}</p>'
        + "".join(
            f'<p style="margin-bottom:3px;"><b>{html.escape(t["name"])}</b> '
            f'<span class="chan">{html.escape(t["domain"])}</span> — {html.escape(t["tagline"])} '
            f'<span class="num" style="color:{ui.SLATE};">{t["win_rate"]:.0%}</span></p>'
            for t in strengths["bottom"]
        ),
    )

    result = st.session_state.results["strengths_core"].summary
    with st.expander(f"Classement complet des {len(result['ranking'])} thèmes"):
        for rank, name in enumerate(result["ranking"], start=1):
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;font-size:0.92rem;'
                f'padding:2px 0;border-bottom:1px solid {ui.RULE};">'
                f'<span><span class="num">{rank:02d}</span> {html.escape(name)}</span>'
                f'<span class="num" style="color:{ui.SLATE};">{result["win_rates"][name]:.0%} '
                f'({result["wins"][name]}/{result["exposure"][name]})</span></div>',
                unsafe_allow_html=True,
            )


def _stress_section(report: dict) -> None:
    stress = report["stress"]
    st.markdown("## Sous pression")
    dominant = stress["dominant"]
    st.markdown(
        f'<div class="panel"><h4>{MODE_LABELS[dominant]}</h4>'
        f'<p>{html.escape(MODE_BLURBS[dominant])}</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "".join(
            ui.errorbar(MODE_LABELS[mode], stress["scores"][mode],
                        stress["standard_error"][mode], ui.SIGNAL)
            for mode in stress["ranking"]
        ),
        unsafe_allow_html=True,
    )
    with st.expander("Pourquoi ? — les réponses derrière votre mode sous pression"):
        _likert_evidence(report["stress_evidence"][dominant])


def _motivator_section(report: dict) -> None:
    motivators = report["motivators"]
    st.markdown("## Ce qui vous motive")
    st.markdown(
        '<div class="chan">Taux de victoire sur 28 duels · chaque moteur a affronté chacun des autres une fois</div>',
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        "".join(
            ui.errorbar(driver, motivators["win_rates"][driver] * 100,
                        motivators["standard_error"][driver] * 100, ui.SIGNAL, suffix="%")
            for driver in motivators["ranking"]
        ),
        unsafe_allow_html=True,
    )
    top = motivators["top"][0]
    ui.panel(top, f'<p>{html.escape(DRIVER_BLURBS[top])}</p>')
    with st.expander("Pourquoi ? — les arbitrages derrière votre moteur principal"):
        _choice_evidence([e for e in report["motivator_evidence"][top] if e["chosen"]][:5])


def _drift_section() -> None:
    drift = state.drift()
    if not drift:
        return
    st.markdown("## Évolution depuis la dernière fois")
    if drift["legacy"]:
        st.caption(
            "Le passage précédent provient d'une version antérieure de cette application, qui "
            "n'enregistrait pas la marge d'erreur. Les écarts ci-dessous ne peuvent pas être "
            "comparés au bruit de mesure."
        )
    rows = []
    for style, move in drift["moves"].items():
        verdict = "un changement réel" if move["real"] else "dans la marge de bruit"
        rows.append(
            f'<p><b>{STYLE_NAMES[style]}</b> '
            f'<span class="num">{move["before"]:.0f} → {move["after"]:.0f} ({move["delta"]:+.0f})</span> '
            f'<span class="chan">· {verdict}</span></p>'
        )
    ui.panel(f"Comparé au {drift['date'][:10]}", "".join(rows))
    st.caption(
        "La plupart des écarts entre deux passages ne sont que du bruit de mesure. Un changement n'est "
        "considéré comme réel que s'il dépasse l'erreur combinée des deux mesures."
    )


def _plan_section(report: dict) -> None:
    if not report["plan"]:
        return
    st.markdown("## Trois choses à essayer cette semaine")
    for experiment in report["plan"]:
        st.markdown(
            f'<div class="panel"><div class="chan">{html.escape(experiment["why"])}</div>'
            f'<h4 style="margin-top:6px;">{html.escape(experiment["title"])}</h4>'
            f'<p>{html.escape(experiment["body"])}</p></div>',
            unsafe_allow_html=True,
        )


def _add_modules() -> None:
    remaining = [
        m for m in ADDON_MODULES
        if m not in st.session_state.results
        and all(d in st.session_state.results for d in REGISTRY[m].depends_on)
    ]
    if not remaining:
        return
    st.markdown("## Pour aller plus loin")
    st.caption("Chacun de ces modules ajoute une section ici, et permet des comparaisons que les autres ne permettent pas.")
    for module_id in remaining:
        module = REGISTRY[module_id]
        st.markdown(
            f'<p style="margin-bottom:2px;"><b>{module.icon} {html.escape(module.title)}</b> '
            f'<span class="chan">≈ {module.minutes.get("standard", 5)} min</span><br>'
            f'<span style="color:{ui.SLATE};font-size:0.94rem;">{html.escape(module.blurb)}</span></p>',
            unsafe_allow_html=True,
        )
        if st.button("Faire ce module", key=f"add_{module_id}"):
            state.add_module(module_id, module.variants[0])
            st.rerun()


def _pdf_bytes(report: dict, results: dict) -> bytes:
    """Rendering the PDF costs a matplotlib figure and a full document build, so
    it is kept until the answers (or the identity printed on it) change,
    rather than rebuilt on every rerun."""
    identity = st.session_state.get("identity") or {}
    signature = (tuple(sorted(results)), len(st.session_state.answers), tuple(sorted(identity.items())))
    cached = st.session_state.get("_pdf_cache")
    if cached is None or cached[0] != signature:
        pdf_bytes = build_pdf(report, results, identity).getvalue()
        st.session_state["_pdf_cache"] = (signature, pdf_bytes)
    return st.session_state["_pdf_cache"][1]


def _slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()


def _export_filename(extension: str) -> str:
    """profil-disc-prenom-nom-AAAA-MM-JJ.<ext> — so that when several
    stagiaires' downloads land in the same folder (or the same trainer inbox),
    the file itself says whose it is and from which day, without anyone having
    to rename it by hand."""
    identity = st.session_state.get("identity") or {}
    name_slug = "-".join(
        _slug(identity.get(part, "")) for part in ("prenom", "nom") if _slug(identity.get(part, ""))
    )
    base = "-".join(p for p in ["profil-disc", name_slug, datetime.now().strftime("%Y-%m-%d")] if p)
    return f"{base}.{extension}"


def _sync_to_trainer(report: dict, results: dict) -> None:
    """Send this result to the trainer's Google Sheet: once as soon as
    disc_natural is done, and again whenever an addon module completes
    afterwards (the trainee can add modules from this same results page —
    see _add_modules below, which sends them back through the picker and
    then back here). Each send carries the full up-to-date snapshot, so a
    trainer's sheet ends up with one row per attempt, each richer than the
    last, rather than silently dropping whatever was completed after the
    first sync."""
    if "disc_natural" not in results:
        return
    current_modules = frozenset(results)
    already_synced = st.session_state.get("_synced_modules")
    if already_synced is not None and current_modules <= already_synced:
        return  # nothing new to report since the last send
    identity = st.session_state.get("identity") or {}
    ok, status = sheet_sync.send_result(identity, report, results)
    st.session_state["_synced_modules"] = current_modules
    st.session_state["_sent_to_trainer_status"] = status
    if ok:
        st.caption("✓ Résultat transmis à votre formateur.")
    elif status != "non_configure":
        st.caption(
            "⚠ Le résultat n'a pas pu être transmis automatiquement à votre formateur "
            "(problème technique). Pensez à lui envoyer votre PDF."
        )


def render() -> None:
    results = st.session_state.results
    if not results:
        st.session_state.stage = "picker"
        st.rerun()
        return

    report = build_report(
        results,
        {mid: state.sources(mid) for mid in results},
        {mid: state.source_answers(mid) for mid in results},
    )

    completed = ", ".join(REGISTRY[m].title for m in results)
    ui.masthead("Votre profil", html.escape(completed), eyebrow="Rapport")
    _sync_to_trainer(report, results)
    _confidence_banner(report)

    if "disc" in report:
        _disc_section(report)
    if "strain" in report:
        _strain_section(report)
    if "strengths" in report:
        _strengths_section(report)
    if "stress" in report:
        _stress_section(report)
    if "motivators" in report:
        _motivator_section(report)

    if report["integrations"]:
        st.markdown("## Là où les regards se croisent")
        for section in report["integrations"]:
            ui.panel(section["title"], "".join(f"<p>{line}</p>" for line in section["lines"]),
                     icon=section["icon"])

    _drift_section()
    _plan_section(report)
    _add_modules()

    st.markdown("---")
    st.markdown('<div class="chan">Conservez vos résultats</div>', unsafe_allow_html=True)
    st.caption(
        "Le fichier JSON contient vos réponses : vous pouvez reprendre plus tard, ajouter des modules, "
        "ou comparer un futur passage à celui-ci. En dehors du résultat transmis à votre formateur "
        "(nom, prénom, session et scores DISC), rien n'est stocké sur un serveur."
    )
    left, middle, right = st.columns(3)
    with left:
        st.download_button(
            "Télécharger le JSON",
            data=json.dumps(state.export_payload(), indent=2),
            file_name=_export_filename("json"),
            mime="application/json",
            use_container_width=True,
        )
    with middle:
        st.download_button(
            "Télécharger le PDF",
            data=_pdf_bytes(report, results),
            file_name=_export_filename("pdf"),
            mime="application/pdf",
            use_container_width=True,
        )
    with right:
        if st.button("Recommencer", key="reset", use_container_width=True):
            state.reset()
            st.rerun()
