"""Unit tests for the Google Sheet webhook integration.

No network call is made here: send_result must be a safe no-op when the
webhook secret isn't configured (the default state for a fresh checkout).
"""
from __future__ import annotations

from app import sheet_sync


def test_webhook_url_is_none_without_secrets_file():
    assert sheet_sync.webhook_url() is None


def test_send_result_is_a_safe_noop_when_unconfigured():
    identity = {"prenom": "Ada", "nom": "Lovelace", "session": "Gestion du temps"}
    report = {"disc": {"title": "Style Dominance (D)"}}
    summary = {
        "normalized": {"D": 70.0, "I": 50.0, "S": 40.0, "C": 45.0},
        "style_code": "D",
        "intensity": "Marquée",
    }
    ok, status = sheet_sync.send_result(identity, report, summary, "Moderate")
    assert ok is False
    assert status == "non_configure"


def test_build_payload_shape():
    identity = {"prenom": "Ada", "nom": "Lovelace", "session": "Gestion du temps"}
    report = {"disc": {"title": "Style Dominance (D)"}}
    summary = {
        "normalized": {"D": 70.0, "I": 50.0, "S": 40.0, "C": 45.0},
        "style_code": "D",
        "intensity": "Marquée",
    }
    payload = sheet_sync.build_payload(identity, report, summary, "High")
    assert payload["prenom"] == "Ada"
    assert payload["nom"] == "Lovelace"
    assert payload["session"] == "Gestion du temps"
    assert payload["style_code"] == "D"
    assert payload["style_titre"] == "Style Dominance (D)"
    assert payload["confiance"] == "High"
    assert payload["score_D"] == 70.0
    assert "horodatage" in payload
