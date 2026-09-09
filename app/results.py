"""The report. Every claim is followed by the answers that produced it."""

from __future__ import annotations

import html
import json

import streamlit as st

from assessment.registry import ADDON_MODULES, REGISTRY
from assessment.report.build import build_report
from assessment.scoring.disc import STYLE_NAMES
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
    st.markdown("## Natural vs. at work")
    st.markdown(
        f'<span class="tag">strain index · <span class="num">{strain["index"]:.0f}</span></span>'
        f'<span class="tag">{strain["band"]} adaptation load</span>',
        unsafe_allow_html=True,
    )
    st.write("")
    rows = []
    for style in "DISC":
        shift = strain["shifts"][style]
        marker = "significant" if shift["significant"] else "within noise"
        rows.append(
            f'<p><b>{STYLE_NAMES[style]}</b> '
            f'<span class="num">{shift["natural"]:.0f} → {shift["adaptive"]:.0f} '
            f'({shift["delta"]:+.0f})</span> '
            f'<span class="chan">· {marker}</span></p>'
        )
    ui.panel("What the role asks of you", "".join(rows))
    st.caption(
        "A shift marked *within noise* is smaller than the measurement error and should not be "
        "read as a real difference."
    )


def _strengths_section(report: dict) -> None:
    strengths = report["strengths"]
    st.markdown("## Signature strengths")
    st.markdown(f'<div class="panel"><p>{strengths["tie_note"]}</p></div>', unsafe_allow_html=True)

    st.markdown('<div class="chan">Domain balance</div>', unsafe_allow_html=True)
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
                <span class="num">chosen {theme['wins']}/{theme['exposure']} times offered</span></div>
              <div class="theme-name">{html.escape(theme['name'])}</div>
              <p style="color:{ui.SLATE};margin:4px 0 8px 0;">{html.escape(theme['tagline'])}</p>
              <p style="margin:0 0 8px 0;">{html.escape(theme['description'])}</p>
              <p style="margin:0;font-size:0.94rem;"><b>Use it:</b> {html.escape(theme['action'])}</p>
              <div class="theme-cost">
                <b>How it lands.</b> {html.escape(theme['shadow'])}<br>
                <b>When it costs you.</b> {html.escape(theme['overuse'])}
              </div>
            </div>""",
            unsafe_allow_html=True,
        )
        with st.expander(f"Why {theme['name']}? — the choices behind it"):
            _choice_evidence(theme["evidence"])

    with st.expander("Supporting themes (#6–#10)"):
        for rank, theme in enumerate(strengths["supporting"], start=6):
            st.markdown(
                f"**#{rank} {theme['name']}** *({theme['domain']})* — {theme['tagline']} "
                f"`{theme['win_rate']:.0%}`"
            )

    ui.panel(
        "What you deprioritise",
        f'<p>{html.escape(strengths["bottom_note"])}</p>'
        + "".join(
            f'<p style="margin-bottom:3px;"><b>{html.escape(t["name"])}</b> '
            f'<span class="chan">{html.escape(t["domain"])}</span> — {html.escape(t["tagline"])} '
            f'<span class="num" style="color:{ui.SLATE};">{t["win_rate"]:.0%}</span></p>'
            for t in strengths["bottom"]
        ),
    )

    with st.expander("Full ranking of all 34 themes"):
        result = st.session_state.results["strengths_core"].summary
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
    st.markdown("## Under pressure")
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
    with st.expander("Why this? — the answers behind your pressure mode"):
        _likert_evidence(report["stress_evidence"][dominant])


def _motivator_section(report: dict) -> None:
    motivators = report["motivators"]
    st.markdown("## What drives you")
    st.markdown(
        '<div class="chan">Win rate across 28 head-to-head trades · every driver met every other once</div>',
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
    with st.expander("Why this? — the trades behind your top driver"):
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
    st.markdown("## Go further")
    st.caption("Each of these adds a section here, and unlocks comparisons the others cannot make.")
    for module_id in remaining:
        module = REGISTRY[module_id]
        st.markdown(
            f'<p style="margin-bottom:2px;"><b>{module.icon} {html.escape(module.title)}</b> '
            f'<span class="chan">≈ {module.minutes.get("standard", 5)} min</span><br>'
            f'<span style="color:{ui.SLATE};font-size:0.94rem;">{html.escape(module.blurb)}</span></p>',
            unsafe_allow_html=True,
        )
        if st.button(f"Take it", key=f"add_{module_id}"):
            state.add_module(module_id, module.variants[0])
            st.rerun()


def _pdf_bytes(report: dict, results: dict) -> bytes:
    """Rendering the PDF costs a matplotlib figure and a full document build, so
    it is kept until the answers change rather than rebuilt on every rerun."""
    signature = (tuple(sorted(results)), len(st.session_state.answers))
    cached = st.session_state.get("_pdf_cache")
    if cached is None or cached[0] != signature:
        st.session_state["_pdf_cache"] = (signature, build_pdf(report, results).getvalue())
    return st.session_state["_pdf_cache"][1]


def _sync_to_trainer(report: dict, results: dict) -> None:
    """Send this result to the trainer's Google Sheet once, the first time the
    results page is reached with a finished disc_natural module."""
    if "disc_natural" not in results or st.session_state.get("_sent_to_trainer"):
        return
    identity = st.session_state.get("identity") or {}
    summary = results["disc_natural"].summary
    confidence_level = report["confidence"].get("disc_natural", {}).get("level", "Moderate")
    ok, status = sheet_sync.send_result(identity, report, summary, confidence_level)
    st.session_state["_sent_to_trainer"] = True
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
            file_name="profil-disc.json",
            mime="application/json",
            use_container_width=True,
        )
    with middle:
        st.download_button(
            "Télécharger le PDF",
            data=_pdf_bytes(report, results),
            file_name="rapport-disc.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with right:
        if st.button("Recommencer", key="reset", use_container_width=True):
            state.reset()
            st.rerun()
