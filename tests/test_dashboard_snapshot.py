"""Unit tests for dashboard snapshot parsers (EU summaryInfo layout)."""

from coros_api import (
    _parse_run_score_list,
    _pick_recovery,
    _pick_running_form,
    _pick_race_predict,
)


def test_pick_running_form_eu_scores():
    summary = {
        "staminaLevel": 91.2,
        "aerobicEnduranceScore": 90.7,
        "lactateThresholdCapacityScore": 90.3,
        "anaerobicEnduranceScore": 90.3,
        "anaerobicCapacityScore": 90.3,
    }
    form = _pick_running_form(summary, {})
    assert form["total"] == 91.2
    assert form["endurance"] == 90.7
    assert form["threshold"] == 90.3
    assert form["speed"] == 90.3
    assert form["sprint"] == 90.3


def test_pick_recovery_eu_flat_keys():
    summary = {"recoveryPct": 59, "recoveryState": 2, "fullRecoveryHours": 54}
    rec = _pick_recovery(summary)
    assert rec["recovery_percent"] == 59
    assert rec["recovery_state"] == 2
    assert rec["full_recovery_hours"] == 54


def test_parse_run_score_list():
    raw = [
        {"type": 5, "duration": 1148, "avgPace": 230},
        {"type": 1, "duration": 10932, "avgPace": 259},
    ]
    out = _parse_run_score_list(raw)
    assert out[0]["distance"] == "marathon"
    assert out[0]["time_seconds"] == 10932
    assert out[1]["distance"] == "5k"


def test_pick_race_predict_prefers_run_score_list():
    summary = {
        "runScoreList": [{"type": 4, "duration": 2369, "avgPace": 237}],
    }
    assert _pick_race_predict(summary, {})[0]["distance"] == "10k"
