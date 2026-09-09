"""Unit tests for the Google Sheet webhook integration.

The "unconfigured" tests make no network call by construction. The others
stub out ``requests.get`` — real network access from this suite would be
both slow and dependent on a live Apps Script deployment.
"""
from __future__ import annotations

import requests

from app import sheet_sync

_IDENTITY = {"prenom": "Ada", "nom": "Lovelace", "session": "Gestion du temps"}
_REPORT = {"disc": {"title": "Style Dominance (D)"}}
_SUMMARY = {
    "normalized": {"D": 70.0, "I": 50.0, "S": 40.0, "C": 45.0},
    "style_code": "D",
    "intensity": "Marquée",
}


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


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


def test_send_result_uses_get_not_post(monkeypatch):
    """A POST to an Apps Script /exec URL gets redirected and silently
    downgraded to a bodyless GET by requests' own redirect handling — see the
    comment in sheet_sync.send_result. Sending a GET from the start is what
    sidesteps that, so this project must never regress back to requests.post
    here."""
    monkeypatch.setattr(sheet_sync, "webhook_url", lambda: "https://example.com/exec")
    calls = []

    def fake_get(url, params=None, timeout=None):
        calls.append((url, params, timeout))
        return _FakeResponse(200)

    monkeypatch.setattr(sheet_sync.requests, "get", fake_get)
    monkeypatch.setattr(
        sheet_sync.requests,
        "post",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not POST")),
    )

    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _SUMMARY, "Moderate")
    assert ok is True
    assert status == "ok"
    assert len(calls) == 1
    url, params, timeout = calls[0]
    assert url == "https://example.com/exec"
    assert params["prenom"] == "Ada"
    assert params["score_D"] == 70.0


def test_send_result_reports_http_errors(monkeypatch):
    monkeypatch.setattr(sheet_sync, "webhook_url", lambda: "https://example.com/exec")
    monkeypatch.setattr(
        sheet_sync.requests, "get",
        lambda *a, **k: _FakeResponse(500, "Script error: doPost is not defined"),
    )
    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _SUMMARY, "Moderate")
    assert ok is False
    assert status == "erreur_http_500"


def test_send_result_reports_network_errors(monkeypatch):
    monkeypatch.setattr(sheet_sync, "webhook_url", lambda: "https://example.com/exec")

    def raise_it(*a, **k):
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(sheet_sync.requests, "get", raise_it)
    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _SUMMARY, "Moderate")
    assert ok is False
    assert status.startswith("erreur_reseau")
