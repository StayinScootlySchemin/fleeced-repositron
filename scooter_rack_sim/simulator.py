from __future__ import annotations

from dataclasses import dataclass

from .models import Config, LayoutResult


@dataclass(frozen=True)
class Rect:
    min_x: float
    max_x: float
    min_y: float
    max_y: float


@dataclass(frozen=True)
class LayoutCandidate:
    holes: tuple[int, ...]
    lane_spacing: float
    stagger_offset: float


def rectangles_overlap(a: Rect, b: Rect, clearance: float = 0.0) -> bool:
    return not (
        a.max_x + clearance <= b.min_x
        or b.max_x + clearance <= a.min_x
        or a.max_y + clearance <= b.min_y
        or b.max_y + clearance <= a.min_y
    )


def width_feasible(config: Config) -> tuple[bool, str]:
    usable_width = config.rack.width + 2 * config.constraints.allowed_overhang
    required = config.scooter.handlebar_width + 2 * config.constraints.side_clearance
    return usable_width >= required, f"width usable={usable_width:.1f}, required={required:.1f}"


def depth_feasible(config: Config) -> tuple[bool, str]:
    usable_depth = config.rack.depth + config.constraints.allowed_overhang
    required = (
        config.scooter.deck_length
        + config.constraints.front_clearance
        + config.constraints.rear_clearance
    )
    return usable_depth >= required, f"depth usable={usable_depth:.1f}, required={required:.1f}"


def height_feasible(config: Config) -> tuple[bool, str]:
    usable_height = config.rack.height
    required = config.scooter.deck_height + config.constraints.top_clearance
    return usable_height >= required, f"height usable={usable_height:.1f}, required={required:.1f}"


def evaluate_feasibility(config: Config) -> tuple[bool, tuple[str, ...]]:
    checks = [width_feasible(config), depth_feasible(config), height_feasible(config)]
    feasible = all(ok for ok, _ in checks)
    notes = tuple(note for _, note in checks)
    return feasible, notes


def _generate_holes(config: Config) -> list[int]:
    count = int(config.rack.width // config.hole_pitch) + 1
    unusable = set(config.unusable_holes)
    return [idx for idx in range(count) if idx not in unusable]


def _deck_rect(center_x: float, config: Config) -> Rect:
    half_w = config.scooter.deck_width / 2
    return Rect(
        min_x=center_x - half_w,
        max_x=center_x + half_w,
        min_y=0.0,
        max_y=config.scooter.deck_length,
    )


def _handlebar_rect(center_x: float, stagger_offset: float, config: Config) -> Rect:
    half_w = config.scooter.handlebar_width / 2
    bar_depth = max(40.0, config.scooter.deck_length * 0.1)
    start_y = config.scooter.stem_offset + stagger_offset
    return Rect(
        min_x=center_x - half_w,
        max_x=center_x + half_w,
        min_y=start_y,
        max_y=start_y + bar_depth,
    )


def _pair_jam_risk(x1: float, x2: float, stagger_offset: float, config: Config) -> float:
    deck1 = _deck_rect(x1, config)
    deck2 = _deck_rect(x2, config)
    bar1 = _handlebar_rect(x1, 0.0, config)
    bar2 = _handlebar_rect(x2, stagger_offset, config)

    risk = 0.0
    for rect_a, rect_b, weight in [
        (deck1, deck2, 0.2),
        (deck1, bar2, 0.8),
        (bar1, deck2, 0.8),
        (bar1, bar2, 1.0),
    ]:
        if rectangles_overlap(rect_a, rect_b, clearance=0.0):
            risk += weight

    lateral_gap = abs(x2 - x1) - config.scooter.handlebar_width
    if lateral_gap > config.constraints.side_clearance:
        risk *= 0.6
    elif lateral_gap > 0:
        risk *= 0.85

    return min(1.0, risk / 2.8)


def _layout_jam_risk(centers: list[float], stagger_offset: float, config: Config) -> float:
    if len(centers) < 2:
        return 0.0
    pair_scores = [
        _pair_jam_risk(a, b, stagger_offset, config)
        for a, b in zip(centers[:-1], centers[1:])
    ]
    return sum(pair_scores) / len(pair_scores)


def _access_factor(config: Config) -> float:
    sides = set(config.constraints.access_sides)
    if sides == {"left", "right"}:
        return 1.0
    if sides & {"left", "right"}:
        return 0.9
    return 0.75


def _generate_candidates(config: Config, holes: list[int]) -> list[LayoutCandidate]:
    candidates: list[LayoutCandidate] = []
    for lane_spacing_holes in range(1, min(8, len(holes)) + 1):
        selected_holes = tuple(holes[::lane_spacing_holes])
        if not selected_holes:
            continue
        spacing_mm = lane_spacing_holes * config.hole_pitch
        for stagger in config.constraints.stagger_offsets:
            candidates.append(
                LayoutCandidate(
                    holes=selected_holes,
                    lane_spacing=spacing_mm,
                    stagger_offset=stagger,
                )
            )
    return candidates


def simulate_layouts(config: Config) -> list[LayoutResult]:
    feasible, notes = evaluate_feasibility(config)
    if not feasible:
        return [
            LayoutResult(
                layout_id=1,
                active_capacity=0,
                jam_risk=1.0,
                lane_spacing=0.0,
                stagger_offset=0.0,
                holes=tuple(),
                feasibility_notes=notes,
            )
        ]

    holes = _generate_holes(config)
    if not holes:
        return []

    results: list[LayoutResult] = []
    access_factor = _access_factor(config)

    for layout_id, candidate in enumerate(_generate_candidates(config, holes), start=1):
        selected_centers = [h * config.hole_pitch for h in candidate.holes]
        jam = _layout_jam_risk(selected_centers, candidate.stagger_offset, config)
        raw_capacity = len(candidate.holes) * access_factor
        active_capacity = int(max(0, round(raw_capacity * (1.0 - 0.5 * jam))))

        results.append(
            LayoutResult(
                layout_id=layout_id,
                active_capacity=active_capacity,
                jam_risk=round(jam, 4),
                lane_spacing=candidate.lane_spacing,
                stagger_offset=candidate.stagger_offset,
                holes=candidate.holes,
                feasibility_notes=notes,
            )
        )

    results.sort(key=lambda r: (-r.active_capacity, r.jam_risk, -r.lane_spacing))
    return results[: config.top_n]


def build_sheet(layout: LayoutResult, config: Config) -> str:
    marks = [f"H{hole}:{hole * config.hole_pitch:.0f}mm" for hole in layout.holes]
    return "\n".join(
        [
            f"Layout #{layout.layout_id}",
            f"Capacity: {layout.active_capacity}",
            f"Jam risk: {layout.jam_risk:.3f}",
            f"Lane spacing: {layout.lane_spacing:.1f} mm",
            f"Stagger offset: {layout.stagger_offset:.1f} mm",
            f"Shelf hole numbers: {', '.join(f'H{h}' for h in layout.holes) or 'none'}",
            f"Lane spacing marks: {', '.join(marks) or 'none'}",
        ]
    )
