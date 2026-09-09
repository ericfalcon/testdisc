"""End-to-end runs of the real Streamlit app, headless.

Covers what unit tests cannot: the item queue, the forward-only advance, the
results page rendering, and the JSON round trip.

Note on structure: a stage change goes through ``st.rerun``, which leaves the
previous screen's widgets in AppTest's element tree and breaks the following
run. Tests that need to exercise the questionnaire therefore seed the stage
through the app's own state helpers instead of clicking through the picker; the
picker's own transition is covered separately.

This French edition keeps only the "disc_natural" module (see
assessment/registry.py) — the strengths/stress/motivators modules of the
upstream project mirror Gallup's trademarked CliftonStrengths taxonomy and
were dropped rather than translated. Tests below were trimmed to match.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from streamlit.testing.v1 import AppTest

TIMEOUT = 120
# AppTest resolves a relative path against the calling file's directory.
APP = str(Path(__file__).resolve().parent.parent / "disc_style.py")


def _blank() -> AppTest:
    return AppTest.from_file(APP, default_timeout=TIMEOUT)


def _app() -> AppTest:
    app = _blank()
    app.run()
    return app


def _with_state(app: AppTest, call):
    """Run one of the app's own state helpers against the test session."""
    original = st.session_state
    try:
        st.session_state = app.session_state  # type: ignore[assignment]
        return call()
    finally:
        st.session_state = original  # type: ignore[assignment]


def _started(modules: dict[str, str], seed: int = 42) -> AppTest:
    """An app sitting on the first question of the given modules."""
    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    app.session_state["seed"] = seed
    _with_state(app, lambda: app_state.build_queue(modules))
    app.session_state["stage"] = "running"
    app.run()
    return app


def _answer_current(app: AppTest, choice: int) -> None:
    """Set the response and re-run once: the Suivant button is disabled until
    an answer is picked, so its `.disabled` flag must reflect this choice
    before a caller can click it."""
    item = app.session_state.flat[app.session_state.position]
    radio = app.radio(key=f"resp_{item.uid}")
    radio.set_value(radio.options[min(choice, len(radio.options) - 1)])
    app.run()


def _answer_everything(app: AppTest, choice: int = 3) -> AppTest:
    guard = 0
    while app.session_state.stage == "running":
        guard += 1
        assert guard < 400, "the runner did not terminate"
        _answer_current(app, choice)
        app.button(key="advance").click()
        app.run()
    return app


# --------------------------------------------------------------------- picker

def test_picker_offers_the_disc_module_and_starts_the_queue():
    app = _app()
    keys = {c.key for c in app.checkbox}
    assert keys == {"pick_disc_natural"}
    # The identification fields and the submit button live in one st.form, so
    # setting all three and clicking Commencer can be queued together and
    # read in a single run — no intermediate run() is needed to "commit" each
    # field first, the way plain text_input widgets outside a form would.
    app.text_input(key="id_prenom").set_value("Ada")
    app.text_input(key="id_nom").set_value("Lovelace")
    app.text_input(key="id_session").set_value("Gestion du temps — test")
    app.button(key="begin").click()
    app.run()
    assert app.session_state.stage == "running"
    assert len(app.session_state.flat) == 40


def test_begin_button_requires_identification_before_advancing():
    """The Commencer button is inside a form, so it's always clickable (no
    disabled state to fight with while typing) — the guarantee that the test
    cannot start without a name and session is enforced after the click
    instead, via a warning that keeps the stage on "picker"."""
    app = _app()
    app.button(key="begin").click()
    app.run()
    assert app.session_state.stage == "picker"
    assert app.warning
    assert app.session_state.stage == "picker"


# --------------------------------------------------------------------- runner

def test_advancing_without_an_answer_is_refused():
    """The Suivant button cannot be clicked at all until a response is chosen —
    the same guarantee the disabled Commencer button gives on the picker."""
    app = _started({"disc_natural": "standard"})
    assert app.button(key="advance").disabled
    assert app.session_state.position == 0, "the queue must not advance"
    assert not app.session_state.answers


def test_the_queue_only_moves_forward():
    app = _started({"disc_natural": "standard"})
    positions = []
    for _ in range(4):
        positions.append(app.session_state.position)
        _answer_current(app, 3)
        app.button(key="advance").click()
        app.run()
    assert positions == [0, 1, 2, 3]
    assert all(b.label != "Back" for b in app.button)
    assert len(app.session_state.answers) == 4


def test_each_item_is_shown_once_and_only_once():
    app = _started({"disc_natural": "standard"})
    seen = []
    while app.session_state.stage == "running":
        seen.append(app.session_state.flat[app.session_state.position].uid)
        _answer_current(app, 0)
        app.button(key="advance").click()
        app.run()
    assert len(seen) == len(set(seen)) == 40


# -------------------------------------------------------------------- results

def test_a_full_run_produces_a_report():
    app = _answer_everything(_started({"disc_natural": "standard"}))
    assert app.session_state.stage == "results"
    assert set(app.session_state.results) == {"disc_natural"}
    assert not app.exception

    body = " ".join(m.value for m in app.markdown)
    assert "Votre profil" in body
    assert "Trois choses à essayer cette semaine" in body


def test_uniform_answers_surface_the_low_confidence_warning():
    """A responder who agrees with everything must be told so, prominently."""
    app = _answer_everything(_started({"disc_natural": "standard"}), choice=4)
    assert app.session_state.stage == "results"
    body = " ".join(m.value for m in app.markdown)
    assert "Confiance faible" in body


# ------------------------------------------------------------------ portability

def test_export_round_trips_through_import():
    from app import state as app_state

    app = _answer_everything(_started({"disc_natural": "standard"}), choice=2)
    payload = json.loads(json.dumps(_with_state(app, app_state.export_payload)))
    assert payload["schema_version"] == 2
    assert payload["modules"]["disc_natural"]["answers"]
    assert payload["history"]

    fresh = _blank()
    _with_state(fresh, app_state.init)
    _with_state(fresh, lambda: app_state.load_payload(payload))
    assert fresh.session_state.stage == "results"
    before = app.session_state.results["disc_natural"].summary["normalized"]
    after = fresh.session_state.results["disc_natural"].summary["normalized"]
    assert before == after, "reloading a profile must reproduce the same scores"


def test_a_partial_run_resumes_where_it_stopped():
    from app import state as app_state

    app = _started({"disc_natural": "standard"})
    for _ in range(5):
        _answer_current(app, 0)
        app.button(key="advance").click()
        app.run()
    payload = _with_state(app, app_state.export_payload)

    fresh = _blank()
    _with_state(fresh, app_state.init)
    _with_state(fresh, lambda: app_state.load_payload(payload))
    assert fresh.session_state.position == 5
    assert fresh.session_state.stage == "running", "a partial run must resume, not restart"
    assert len(fresh.session_state.flat) == 40


def test_a_legacy_export_is_kept_for_comparison():
    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    message = _with_state(
        app,
        lambda: app_state.load_payload(
            {"disc": {"normalized_scores": {"D": 70, "I": 50, "S": 40, "C": 45}}}
        ),
    )
    assert "version antérieure" in message
    assert app.session_state.history[0]["legacy"] is True


def test_an_unrecognised_file_is_rejected():
    import pytest

    from app import state as app_state

    app = _blank()
    _with_state(app, app_state.init)
    with pytest.raises(ValueError, match="pas un export de test valide"):
        _with_state(app, lambda: app_state.load_payload({"unrelated": True}))
