"""Module selection. Everything is opt-in and states its own cost up front."""

from __future__ import annotations

import html
import json

import streamlit as st

from assessment.registry import ADDON_MODULES, CORE_MODULES, REGISTRY

from . import components as ui
from . import state


def _module_row(module_id: str, default: bool) -> tuple[bool, str]:
    module = REGISTRY[module_id]
    label = f"{module.icon}  {module.title}"

    # Dependencies used to be enforced by hiding the checkbox behind blocked
    # text until the prerequisite module was checked elsewhere in the same
    # render — but every widget here lives inside `st.form`, and Streamlit
    # forms explicitly do not rerun the script (and so never re-evaluate that
    # "is the prerequisite checked" condition) until the whole form is
    # submitted. A checkbox that can only unblock on a rerun that never
    # happens can never be checked — confirmed live: ticking "Vos moteurs
    # profonds" never unblocked "Votre instinct dominant" underneath it. The
    # checkbox is now always clickable; the dependency is enforced instead at
    # submit time, below, by silently adding whatever it needs.
    picked = st.checkbox(label, value=default, key=f"pick_{module_id}")
    variant = module.variants[0]
    if picked and len(module.variants) > 1:
        variant = st.radio(
            "Durée",
            options=list(module.variants),
            format_func=lambda v: module.variant_labels.get(v, v),
            key=f"variant_{module_id}",
            label_visibility="collapsed",
        )
    minutes = module.minutes.get(variant, 5)
    needs_note = ""
    if module.depends_on:
        needs = ", ".join(REGISTRY[d].title for d in module.depends_on)
        needs_note = (
            f'<br><span class="chan">nécessite {html.escape(needs)} — '
            f"ajouté automatiquement si vous cochez celui-ci sans lui</span>"
        )
    st.markdown(
        f'<div style="margin:-6px 0 14px 30px;color:{ui.SLATE};font-size:0.93rem;line-height:1.55;">'
        f'{html.escape(module.blurb)}<br><span class="chan">≈ {minutes} min</span>{needs_note}</div>',
        unsafe_allow_html=True,
    )
    return picked, variant


def _identification() -> dict[str, str]:
    st.markdown('<div class="chan">Étape 1 · Vos informations</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    with cols[0]:
        prenom = st.text_input("Prénom", key="id_prenom")
    with cols[1]:
        nom = st.text_input("Nom", key="id_nom")
    session = st.text_input(
        "Session / formation",
        key="id_session",
        placeholder="ex. Gestion du temps — 12 novembre",
    )
    st.caption(
        "Votre nom, prénom et votre profil DISC seront transmis à votre formateur pour préparer "
        "la session. Rien d'autre n'est partagé."
    )
    identity = {"prenom": prenom.strip(), "nom": nom.strip(), "session": session.strip()}
    st.session_state["identity"] = identity
    return identity


def render() -> None:
    ui.masthead(
        "Votre profil DISC, en quelques minutes",
        "Un profil comportemental présenté avec sa marge d'incertitude — y compris quand les "
        "chiffres sont trop proches pour trancher.",
        eyebrow="Test · avant la formation",
    )

    ui.panel(
        "Comment ça se passe",
        "<p>Ce test mesure votre style de comportement : comment vous décidez, communiquez et "
        "réagissez au quotidien. Il n'y a pas de bonne ou de mauvaise réponse — répondez avec ce "
        "qui vous ressemble le plus, pas ce qui semble le mieux vu.</p>"
        "<p style=\"margin-bottom:0;\">Trois étapes : indiquez qui vous êtes, choisissez vos "
        "modules, puis répondez. Le module <b>DISC</b> ci-dessous (≈ 5 min) suffit pour la "
        "formation ; les autres sont facultatifs — ne les ajoutez que si vous voulez aller plus "
        "loin ou que votre formateur vous l'ait demandé.</p>",
        icon="🧭",
    )

    # A form batches the identification fields and the module list so that
    # "Commencer" reads their current content the moment it is clicked —
    # no need to press Enter or click into another field first to "commit"
    # what was just typed, which plain text_input widgets would otherwise
    # require. Enter still works as a shortcut (enter_to_submit, the form
    # default) — it just stops being the only way in.
    with st.form("start_form", border=False):
        identity = _identification()
        st.write("")

        st.markdown(
            '<div class="chan">Étape 2 · Le test DISC (recommandé)</div>', unsafe_allow_html=True
        )
        selection: dict[str, str] = {}
        for module_id in CORE_MODULES:
            picked, variant = _module_row(module_id, default=True)
            if picked:
                selection[module_id] = variant

        if ADDON_MODULES:
            st.markdown(
                '<div class="chan" style="margin-top:0.8rem;">Pour aller plus loin (facultatif)</div>',
                unsafe_allow_html=True,
            )
        for module_id in ADDON_MODULES:
            picked, variant = _module_row(module_id, default=False)
            if picked:
                selection[module_id] = variant

        st.markdown('<div class="chan" style="margin-top:0.8rem;">Étape 3 · C\'est parti</div>', unsafe_allow_html=True)
        submitted = st.form_submit_button(
            "Commencer", key="begin", use_container_width=True, type="primary"
        )

    if submitted:
        # A dependent module (e.g. "Votre instinct dominant") can be picked
        # without its prerequisite being checked in the same pass — the
        # comparison it needs has to come from somewhere, so the prerequisite
        # is added here rather than left to silently produce a hollow result.
        for module_id in list(selection):
            for dep in REGISTRY[module_id].depends_on:
                selection.setdefault(dep, REGISTRY[dep].variants[0])

        missing_identity = not (identity["prenom"] and identity["nom"] and identity["session"])
        if not selection:
            st.warning("Sélectionnez au moins un module pour commencer.")
        elif missing_identity:
            st.warning("Renseignez votre prénom, nom et la session pour commencer.")
        else:
            state.build_queue(selection)
            st.session_state.stage = "running"
            st.rerun()

    with st.expander("Reprendre un profil déjà enregistré"):
        st.caption(
            "Déposez le fichier JSON fourni par cette application. Il restaure vos réponses, vous "
            "permet d'ajouter des modules laissés de côté, et compare un nouveau passage au précédent."
        )
        uploaded = st.file_uploader("Profil enregistré", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            try:
                message = state.load_payload(json.loads(uploaded.getvalue().decode("utf-8")))
                st.success(message)
                st.rerun()
            except (ValueError, KeyError, json.JSONDecodeError) as error:
                st.error(f"Impossible de lire ce fichier : {error}")
