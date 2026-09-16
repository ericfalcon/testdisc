"""Unit tests for the Google Sheet webhook integration.

The "unconfigured" tests make no network call by construction. The others
stub out ``requests.get`` — real network access from this suite would be
both slow and dependent on a live Apps Script deployment.
"""
from __future__ import annotations

import requests

from app import sheet_sync
from assessment.types import ModuleResult

_IDENTITY = {"prenom": "Ada", "nom": "Lovelace", "session": "Gestion du temps"}

_DISC_RESULT = ModuleResult(module_id="disc", summary={
    "normalized": {"D": 70.0, "I": 50.0, "S": 40.0, "C": 45.0},
    "style_code": "D",
    "intensity": "Marquée",
})
_RESULTS = {"disc_natural": _DISC_RESULT}
_REPORT = {
    "disc": {"title": "Style Dominance (D)"},
    "confidence": {"disc_natural": {"level": "Moderate"}},
}

# The same disc_natural result, plus all four addon modules completed — used
# to check that their columns are filled in when present, and that the DISC
# columns are unaffected by their presence.
_ADAPTIVE_RESULT = ModuleResult(module_id="disc", summary={
    "normalized": {"D": 60.0, "I": 55.0, "S": 45.0, "C": 40.0},
    "primary": "I",
})
_STRESS_RESULT = ModuleResult(module_id="stress", summary={"dominant": "retreat"})
_MOTIVATORS_RESULT = ModuleResult(
    module_id="motivators", summary={"top": ["Autonomie", "Sens", "Maîtrise"]}
)
_STRENGTHS_RESULT = ModuleResult(
    module_id="strengths", summary={"top": ["Lancement", "Vision"]}
)
_RESULTS_WITH_ADDONS = {
    "disc_natural": _DISC_RESULT,
    "disc_adaptive": _ADAPTIVE_RESULT,
    "stress_profile": _STRESS_RESULT,
    "motivators": _MOTIVATORS_RESULT,
    "strengths_core": _STRENGTHS_RESULT,
}
_REPORT_WITH_ADDONS = {
    **_REPORT,
    "strain": {"index": 12.3, "band": "moderate", "largest": "I"},
}


class _FakeResponse:
    def __init__(self, status_code: int, text: str = ""):
        self.status_code = status_code
        self.text = text


def test_webhook_url_is_none_without_secrets_file():
    assert sheet_sync.webhook_url() is None


def test_send_result_is_a_safe_noop_when_unconfigured():
    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _RESULTS)
    assert ok is False
    assert status == "non_configure"


def test_build_payload_shape():
    payload = sheet_sync.build_payload(_IDENTITY, _REPORT, _RESULTS)
    assert payload["prenom"] == "Ada"
    assert payload["nom"] == "Lovelace"
    assert payload["session"] == "Gestion du temps"
    assert payload["style_code"] == "D"
    assert payload["style_titre"] == "Style Dominance (D)"
    assert payload["confiance"] == "Moderate"
    assert payload["score_D"] == 70.0
    assert "horodatage" in payload


def test_build_payload_addon_columns_are_blank_without_those_modules():
    """A stagiaire who only did the core DISC module must not get an
    exception, or worse, stray data — every addon column stays a blank
    string so the trainer's sheet reads clearly as "not done"."""
    payload = sheet_sync.build_payload(_IDENTITY, _REPORT, _RESULTS)
    for key in ("style_travail", "indice_tension", "charge_adaptation",
                "mode_sous_pression", "moteurs_principaux", "points_forts_principaux"):
        assert payload[key] == ""


def test_build_payload_includes_completed_addon_modules():
    payload = sheet_sync.build_payload(_IDENTITY, _REPORT_WITH_ADDONS, _RESULTS_WITH_ADDONS)
    assert payload["style_travail"] == "Influence"
    assert payload["indice_tension"] == 12.3
    assert payload["charge_adaptation"] == "modérée"
    assert payload["mode_sous_pression"] == "Retrait"
    assert payload["moteurs_principaux"] == "Autonomie, Sens et Maîtrise"
    assert payload["points_forts_principaux"] == "Lancement et Vision"
    # The core columns are unaffected by the addons riding along.
    assert payload["style_code"] == "D"
    assert payload["score_D"] == 70.0


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

    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _RESULTS)
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
    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _RESULTS)
    assert ok is False
    assert status == "erreur_http_500"


def test_send_result_reports_network_errors(monkeypatch):
    monkeypatch.setattr(sheet_sync, "webhook_url", lambda: "https://example.com/exec")

    def raise_it(*a, **k):
        raise requests.exceptions.Timeout("timed out")

    monkeypatch.setattr(sheet_sync.requests, "get", raise_it)
    ok, status = sheet_sync.send_result(_IDENTITY, _REPORT, _RESULTS)
    assert ok is False
    assert status.startswith("erreur_reseau")
