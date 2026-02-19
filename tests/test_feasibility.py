import json
from pathlib import Path

from scooter_rack_sim.models import Config
from scooter_rack_sim.simulator import depth_feasible, height_feasible, simulate_layouts, width_feasible


def load_example(name: str) -> Config:
    path = Path("examples") / name
    return Config.from_dict(json.loads(path.read_text(encoding="utf-8")))


def test_width_feasible_passes_for_baseline() -> None:
    config = load_example("config_baseline.json")
    ok, _ = width_feasible(config)
    assert ok


def test_depth_feasible_fails_when_deck_is_too_long() -> None:
    config = load_example("config_tight_depth.json")
    ok, _ = depth_feasible(config)
    assert not ok


def test_height_feasible_passes_for_one_sided() -> None:
    config = load_example("config_one_sided_access.json")
    ok, _ = height_feasible(config)
    assert ok


def test_infeasible_config_returns_zero_capacity() -> None:
    config = load_example("config_tight_depth.json")
    results = simulate_layouts(config)
    assert results
    assert results[0].active_capacity == 0
    assert results[0].jam_risk == 1.0


def test_layouts_are_sorted_capacity_then_jam_risk() -> None:
    config = load_example("config_baseline.json")
    results = simulate_layouts(config)
    assert len(results) >= 2
    assert results[0].active_capacity >= results[1].active_capacity
    if results[0].active_capacity == results[1].active_capacity:
        assert results[0].jam_risk <= results[1].jam_risk


def test_stagger_offsets_influence_layouts() -> None:
    config = load_example("config_baseline.json")
    results = simulate_layouts(config)
    stagger_values = {r.stagger_offset for r in results}
    assert stagger_values
