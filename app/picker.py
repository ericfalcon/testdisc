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
    blocked = [d for d in module.depends_on if d not in st.session_state.get("_picked", set())]
    label = f"{module.icon}  {module.title}"

    if blocked:
        # Rendered as text rather than a disabled checkbox: there is nothing to
        # click, and a dead widget only adds noise to the list.
        needs = ", ".join(REGISTRY[d].title for d in blocked)
        st.markdown(
            f'<p style="color:{ui.SLATE};margin-bottom:14px;">{html.escape(label)}<br>'
            f'<span class="chan">nécessite d\'abord {html.escape(needs)} — '
            f'la comparaison n\'a pas de sens sans cela</span></p>',
            unsafe_allow_html=True,
        )
        return False, module.variants[0]

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
    st.markdown(
        f'<div style="margin:-6px 0 14px 30px;color:{ui.SLATE};font-size:0.93rem;line-height:1.55;">'
        f'{html.escape(module.blurb)}<br><span class="chan">≈ {minutes} min</span></div>',
        unsafe_allow_html=True,
    )
    return picked, variant


def _identification() -> dict[str, str]:
    st.markdown('<div class="chan">Avant de commencer</div>', unsafe_allow_html=True)
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

    # A form batches the identification fields and the module list so that
    # "Commencer" reads their current content the moment it is clicked —
    # no need to press Enter or click into another field first to "commit"
    # what was just typed, which plain text_input widgets would otherwise
    # require. Enter still works as a shortcut (enter_to_submit, the form
    # default) — it just stops being the only way in.
    with st.form("start_form", border=False):
        identity = _identification()
        st.write("")

        st.markdown('<div class="chan">Test</div>', unsafe_allow_html=True)
        selection: dict[str, str] = {}
        st.session_state["_picked"] = set()
        for module_id in CORE_MODULES:
            picked, variant = _module_row(module_id, default=True)
            if picked:
                selection[module_id] = variant
                st.session_state["_picked"].add(module_id)

        for module_id in ADDON_MODULES:
            picked, variant = _module_row(module_id, default=False)
            if picked:
                selection[module_id] = variant
                st.session_state["_picked"].add(module_id)

        st.markdown("---")
        submitted = st.form_submit_button(
            "Commencer", key="begin", use_container_width=True, type="primary"
        )

    if submitted:
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
