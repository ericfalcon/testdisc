"""Send a completed DISC result to the trainer's Google Sheet.

The receiving end is a Google Apps Script Web App (see ``docs/apps_script.gs``
in this repo for the code to paste into the target Sheet). This module only
knows how to POST a JSON payload to whatever URL is configured — it has no
Google-specific dependency, so it degrades to a no-op when unconfigured
(local runs, or before the trainer has finished setting up the Sheet).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
import streamlit as st

TIMEOUT_SECONDS = 8


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


def build_payload(identity: dict[str, str], report: dict[str, Any], summary: dict[str, Any],
                   confidence_level: str) -> dict[str, Any]:
    normalized = summary["normalized"]
    return {
        "horodatage": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prenom": identity.get("prenom", ""),
        "nom": identity.get("nom", ""),
        "session": identity.get("session", ""),
        "style_code": summary.get("style_code", ""),
        "style_titre": report.get("disc", {}).get("title", ""),
        "intensite": summary.get("intensity", ""),
        "confiance": confidence_level,
        "score_D": normalized.get("D"),
        "score_I": normalized.get("I"),
        "score_S": normalized.get("S"),
        "score_C": normalized.get("C"),
    }


def send_result(identity: dict[str, str], report: dict[str, Any], summary: dict[str, Any],
                 confidence_level: str) -> tuple[bool, str]:
    """Best-effort POST to the trainer's sheet. Never raises — a network hiccup
    must not block the trainee from seeing their own results."""
    url = webhook_url()
    if not url:
        return False, "non_configure"
    payload = build_payload(identity, report, summary, confidence_level)
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        if response.status_code < 400:
            return True, "ok"
        return False, f"erreur_http_{response.status_code}"
    except requests.RequestException as error:
        return False, f"erreur_reseau: {error}"
