"""Unit tests for structured workout step targets."""

import coros_api


def test_distance_km_target_legacy():
    tt, tv, est = coros_api._resolve_step_target({"distance_km": 14})
    assert tt == 1
    assert tv == 14000
    assert est == 14 * 300


def test_running_hub_distance_centimeters():
    tt, tv, est = coros_api._resolve_step_target(
        {"distance_km": 7}, running_hub=True
    )
    assert tt == 5
    assert tv == 700000
    assert est == 7 * 300


def test_duration_minutes_target():
    tt, tv, est = coros_api._resolve_step_target({"duration_minutes": 1.5})
    assert tt == 2
    assert tv == 90
    assert est == 90


def test_ltsp_percent_fields_threshold_hr():
    ip, ipe = coros_api._ltsp_percent_fields(159, 166, threshold_hr=175)
    assert ip == 91000
    assert ipe == 95000


def test_hr_reserve_percent_fields_z2_easy():
    ip, ipe = coros_api._hr_reserve_percent_fields(
        132, 142, resting_hr=52, max_hr=195
    )
    assert ip == 56000
    assert ipe == 63000


def test_repeat_group_uses_distance_substeps():
    steps = [
        {
            "repeat": 3,
            "steps": [
                {"name": "MP", "distance_km": 3, "intensity_low": 170, "intensity_high": 175},
                {"name": "rest", "duration_minutes": 1.5, "intensity_low": 130, "intensity_high": 145},
            ],
        }
    ]
    total_seconds = 0
    for step in steps:
        sub_sec = sum(coros_api._resolve_step_target(s)[2] for s in step["steps"])
        total_seconds += sub_sec * step["repeat"]
    assert total_seconds == 3 * (3 * 300 + 90)
