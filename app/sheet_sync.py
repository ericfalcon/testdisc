"""Send a completed result to the trainer's Google Sheet.

The DISC module is what triggers the send (see ``_sync_to_trainer`` in
``app/results.py``), and its columns are always filled in. If the stagiaire
has also completed any of the four addon modules by then, a short summary of
each (mode sous pression, moteurs principaux, ...) rides along in the same
row — see ``build_payload``. Nothing beyond a compact, presentation-ready
summary is sent: raw answers, item text and full score breakdowns stay on the
stagiaire's own screen and PDF.

The receiving end is a Google Apps Script Web App (see ``docs/apps_script.gs``
in this repo for the code to paste into the target Sheet). This module only
knows how to GET a URL with the payload in the query string — it has no
Google-specific dependency, so it degrades to a no-op when unconfigured
(local runs, or before the trainer has finished setting up the Sheet).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests
import streamlit as st

from assessment.scoring.disc import STRAIN_BAND_LABELS, STYLE_NAMES
from assessment.scoring.stress import MODE_LABELS
from assessment.types import and_join

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 15


def webhook_url() -> str | None:
    """The Apps Script Web App URL, read from Streamlit secrets.

    Configured on Streamlit Community Cloud under Settings -> Secrets as:

        SHEET_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycb.../exec"
    """
    try:
        return st.secrets.get("SHEET_WEBHOOK_URL")
    except Exception:
        # st.secrets raises if no secrets.toml exists at all (e.g. first local run).
        return None


def build_payload(identity: dict[str, str], report: dict[str, Any],
                   results: dict[str, Any]) -> dict[str, Any]:
    """The DISC columns are always present (this only ever fires once
    disc_natural is done); the four addon columns are sent blank unless that
    module was completed, so a trainer's sheet reads clearly for stagiaires
    who only did the core test."""
    disc = results["disc_natural"].summary
    normalized = disc["normalized"]
    confidence_level = report.get("confidence", {}).get("disc_natural", {}).get("level", "Moderate")

    payload = {
        "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prenom": identity.get("prenom", ""),
        "nom": identity.get("nom", ""),
        "session": identity.get("session", ""),
        "style_code": disc.get("style_code", ""),
        "style_titre": report.get("disc", {}).get("title", ""),
        "intensite": disc.get("intensity", ""),
        "confiance": confidence_level,
        "score_D": normalized.get("D"),
        "score_I": normalized.get("I"),
        "score_S": normalized.get("S"),
        "score_C": normalized.get("C"),
        "style_travail": "",
        "indice_tension": "",
        "charge_adaptation": "",
        "mode_sous_pression": "",
        "moteurs_principaux": "",
        "points_forts_principaux": "",
    }

    if "disc_adaptive" in results:
        adaptive_primary = results["disc_adaptive"].summary.get("primary")
        payload["style_travail"] = STYLE_NAMES.get(adaptive_primary, "")

    strain = report.get("strain")
    if strain:
        payload["indice_tension"] = strain["index"]
        payload["charge_adaptation"] = STRAIN_BAND_LABELS.get(strain["band"], strain["band"])

    if "stress_profile" in results:
        dominant_mode = results["stress_profile"].summary.get("dominant")
        payload["mode_sous_pression"] = MODE_LABELS.get(dominant_mode, "")

    if "motivators" in results:
        payload["moteurs_principaux"] = and_join(results["motivators"].summary.get("top", []))

    if "strengths_core" in results:
        payload["points_forts_principaux"] = and_join(results["strengths_core"].summary.get("top", []))

    return payload


def send_result(identity: dict[str, str], report: dict[str, Any],
                 results: dict[str, Any]) -> tuple[bool, str]:
    """Best-effort call to the trainer's sheet. Never raises — a network hiccup
    must not block the trainee from seeing their own results.

    Sent as a GET with the payload in the query string, not a POST with a JSON
    body. A POST to a Google Apps Script "/exec" URL is answered with an
    internal redirect to a script.googleusercontent.com URL, and — like a
    browser — requests' redirect handling turns that redirected request into
    a GET and drops the body, so Apps Script's doPost() ends up called with no
    request body at all (a TypeError reading e.postData in the Apps Script
    execution log is the signature of exactly this). A GET redirected to a
    GET keeps its query string intact, so it doesn't hit that bug — and the
    payload here is a handful of short fields, comfortably inside URL length
    limits.
    """
    url = webhook_url()
    if not url:
        return False, "non_configure"
    payload = build_payload(identity, report, results)
    params = {key: ("" if value is None else value) for key, value in payload.items()}
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        if response.status_code < 400:
            return True, "ok"
        # Apps Script answers errors with an HTML page, not JSON. The start of
        # that page usually names the real cause (a script exception, a wrong
        # "who has access" setting, ...) — worth capturing here even though
        # the trainee only ever sees a generic message. Visible in Streamlit
        # Community Cloud's "Manage app" log viewer under "Sheet sync".
        snippet = response.text[:300].replace("\n", " ")
        logger.warning(
            "Sheet sync HTTP %s from the Apps Script webhook: %s",
            response.status_code, snippet,
        )
        return False, f"erreur_http_{response.status_code}"
    except requests.RequestException as error:
        logger.warning("Sheet sync network error: %s", error)
        return False, f"erreur_reseau: {error}"
