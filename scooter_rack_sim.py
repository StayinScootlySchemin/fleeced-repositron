"""
scooter_rack_sim.py  (v0)

A small "constrained packing" simulator for storing scooters on adjustable-hole racks.
- Focuses on *counting* + *sanity-checking* your layout before you build it.
- Treats scooters as identical (one model) and uses simple bounding-box style constraints.

Run:
    python scooter_rack_sim.py

Then edit the CONFIG dict at the bottom with your real measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import floor, ceil
from typing import List, Optional, Dict, Any, Tuple


# ----------------------------
# Data model
# ----------------------------

@dataclass(frozen=True)
class Rack:
    """Inside dimensions are the clear usable space BETWEEN uprights at the shelf level."""
    inner_width_in: float
    inner_depth_in: float
    inner_height_in: float

    hole_pitch_in: float = 1.0  # hole-to-hole vertical spacing
    unusable_bottom_holes: int = 0  # e.g., weld blocks first hole(s)
    unusable_top_holes: int = 0     # e.g., top cap blocks last hole(s)

    side_clearance_in: float = 0.0  # clearance each side to avoid rubbing uprights/bolts
    depth_clearance_in: float = 0.0 # clearance front/back inside the footprint


@dataclass(frozen=True)
class Scooter:
    """
    Minimal geometry.
    - deck_width_in should be your "worst case" width INCLUDING kickstand bump.
    - length_in is wheel-to-wheel total footprint when parked upright.
    - height_in is ground-to-handlebar/top.
    """
    deck_width_in: float
    length_in: float
    height_in: float

    # optional for later refinement (not used in v0)
    handlebar_width_in: Optional[float] = None
    weight_lb: Optional[float] = None


@dataclass(frozen=True)
class Constraints:
    """
    Clearances are where most "I missed one thing" bugs live.
    """
    # lateral spacing between scooters (slot pitch = deck_width + slot_clearance)
    slot_clearance_in: float = 0.25

    # extra depth between rows (if you attempt 2 rows inside the footprint)
    row_clearance_in: float = 0.0

    # vertical clearance between levels (shelf-to-shelf), above scooter height
    level_clearance_in: float = 2.0

    # top clearance between top of tallest scooter and rack top
    top_clearance_in: float = 1.0

    # how many depth-rows to consider (1 or 2 is typical)
    max_rows: int = 2

    # optionally clamp the number of levels (e.g., you only want 1-2)
    max_levels: Optional[int] = None

    # 1 means you only access scooters from one side (back row becomes "inactive")
    # 2 means you can access from both sides (front/back), so 2 rows can be active
    access_sides: int = 2

    # allow scooters to hang out beyond the rack depth by this many inches
    # (set to 0 if you must keep everything inside the posts)
    allow_depth_overhang_in: float = 0.0


@dataclass
class LayoutResult:
    lanes_across: int
    rows_depth: int
    levels: int
    shelf_holes: List[int]

    capacity_total: int
    capacity_active: int

    width_leftover_in: float
    depth_leftover_in: float

    notes: List[str] = field(default_factory=list)


# ----------------------------
# Core math
# ----------------------------

def lanes_across(rack: Rack, scooter: Scooter, c: Constraints) -> Tuple[int, float, float]:
    """Return (lanes, usable_width, leftover_width)."""
    usable_w = rack.inner_width_in - 2 * rack.side_clearance_in
    slot_pitch = scooter.deck_width_in + c.slot_clearance_in
    lanes = floor(usable_w / slot_pitch) if slot_pitch > 0 else 0
    used_w = lanes * slot_pitch
    leftover = usable_w - used_w
    return lanes, usable_w, leftover


def rows_depth(rack: Rack, scooter: Scooter, c: Constraints) -> Tuple[int, float, float]:
    """Return (rows, usable_depth, leftover_depth)."""
    usable_d = rack.inner_depth_in - 2 * rack.depth_clearance_in

    eff_len = max(0.0, scooter.length_in - c.allow_depth_overhang_in)
    row_pitch = eff_len + c.row_clearance_in

    rows = 0
    if row_pitch > 0:
        rows = floor(usable_d / row_pitch)

    rows = min(rows, c.max_rows)
    used_d = rows * row_pitch
    leftover = usable_d - used_d
    return rows, usable_d, leftover


def level_step_holes(rack: Rack, scooter: Scooter, c: Constraints) -> int:
    """How many holes between shelf surfaces to fit a scooter + clearance."""
    step_in = scooter.height_in + c.level_clearance_in
    return max(1, ceil(step_in / rack.hole_pitch_in))


def max_levels_and_shelves(rack: Rack, scooter: Scooter, c: Constraints) -> List[Tuple[int, List[int]]]:
    """
    Enumerate feasible (levels, shelf_holes) using the rack's hole grid.
    We assume each level is a shelf at a hole height; scooters stand on that shelf.
    """
    pitch = rack.hole_pitch_in
    bottom = rack.unusable_bottom_holes
    top_limit_in = rack.inner_height_in - c.top_clearance_in

    step = level_step_holes(rack, scooter, c)
    max_levels = c.max_levels or 99

    options: List[Tuple[int, List[int]]] = []
    for L in range(1, max_levels + 1):
        shelves = [bottom + i * step for i in range(L)]
        top_of_last = shelves[-1] * pitch + scooter.height_in
        if top_of_last <= top_limit_in:
            options.append((L, shelves))
        else:
            break
    return options


def simulate(rack: Rack, scooter: Scooter, c: Constraints) -> List[LayoutResult]:
    la, usable_w, w_left = lanes_across(rack, scooter, c)
    rd, usable_d, d_left = rows_depth(rack, scooter, c)

    if la <= 0 or rd <= 0:
        return []

    level_opts = max_levels_and_shelves(rack, scooter, c)
    if not level_opts:
        return []

    results: List[LayoutResult] = []
    for L, shelves in level_opts:
        total = la * rd * L

        notes = []
        active = total
        if c.access_sides <= 1 and rd >= 2:
            active = la * 1 * L
            notes.append("access_sides=1 => back row treated as 'inactive' unless you move scooters.")

        results.append(
            LayoutResult(
                lanes_across=la,
                rows_depth=rd,
                levels=L,
                shelf_holes=shelves,
                capacity_total=total,
                capacity_active=active,
                width_leftover_in=w_left,
                depth_leftover_in=d_left,
                notes=notes,
            )
        )

    # Sort: maximize active, then total, then levels
    results.sort(key=lambda r: (r.capacity_active, r.capacity_total, r.levels), reverse=True)
    return results


# ----------------------------
# Human-friendly "layout hints"
# ----------------------------

def suggested_orientation(rows: int, levels: int) -> List[Dict[str, Any]]:
    """
    Simple heuristics you can use when building:
    - If rows=2 and you can access both sides, store each row facing outward (one row per side).
    - If levels>1, alternate which way scooters face by level to reduce handlebar clashes.
    """
    plan = []
    for lvl in range(1, levels + 1):
        if rows == 1:
            plan.append({"level": lvl, "row1": "outward"})
        else:
            if lvl % 2 == 1:
                plan.append({"level": lvl, "row1": "outward (front side)", "row2": "outward (back side)"})
            else:
                plan.append({"level": lvl, "row1": "outward (back side)", "row2": "outward (front side)"})
    return plan


def requirements_for_target(scooter: Scooter, c: Constraints, target_rows: int, target_levels: int) -> Dict[str, float]:
    """What depth/height you'd minimally need for a desired rows×levels (inside-footprint model)."""
    eff_len = max(0.0, scooter.length_in - c.allow_depth_overhang_in)
    row_pitch = eff_len + c.row_clearance_in
    depth_needed = target_rows * row_pitch

    level_pitch = scooter.height_in + c.level_clearance_in
    height_needed = (target_levels - 1) * level_pitch + scooter.height_in + c.top_clearance_in

    return {"min_depth_in": depth_needed, "min_height_in": height_needed}


# ----------------------------
# Example / quickstart
# ----------------------------

CONFIG: Dict[str, Any] = {
    # Replace these with your real measurements.
    "rack": {
        "inner_width_in": 48.0,
        "inner_depth_in": 48.0,   # measure between uprights front-to-back at shelf height
        "inner_height_in": 70.0,  # measure usable height from shelf surface to top interference
        "hole_pitch_in": 1.0,
        "unusable_bottom_holes": 1,  # if weld blocks the bottom hole
        "unusable_top_holes": 0,
        "side_clearance_in": 0.5,
        "depth_clearance_in": 0.0,
    },
    "scooter": {
        "deck_width_in": 8.5,   # your "call it 8.5 because kickstand bump"
        "length_in": 47.0,      # measure
        "height_in": 45.0,      # measure
    },
    "constraints": {
        "slot_clearance_in": 0.25,
        "row_clearance_in": 0.0,
        "level_clearance_in": 2.0,
        "top_clearance_in": 1.0,
        "max_rows": 2,
        "max_levels": None,
        "access_sides": 2,
        "allow_depth_overhang_in": 0.0,
    },
}


def main() -> None:
    rack = Rack(**CONFIG["rack"])
    scooter = Scooter(**CONFIG["scooter"])
    c = Constraints(**CONFIG["constraints"])

    results = simulate(rack, scooter, c)

    print("\n=== Scooter Rack Packing Simulator (v0) ===\n")
    print("Inputs:")
    print(f"  Rack (W×D×H): {rack.inner_width_in:.1f} × {rack.inner_depth_in:.1f} × {rack.inner_height_in:.1f} in")
    print(f"  Scooter (deckW×L×H): {scooter.deck_width_in:.2f} × {scooter.length_in:.1f} × {scooter.height_in:.1f} in")
    print(f"  slot_clearance: {c.slot_clearance_in:.2f} in, level_clearance: {c.level_clearance_in:.1f} in")
    print(f"  access_sides: {c.access_sides}, allow_depth_overhang: {c.allow_depth_overhang_in:.1f} in")

    la, usable_w, w_left = lanes_across(rack, scooter, c)
    slot_pitch = scooter.deck_width_in + c.slot_clearance_in
    print("\nWidth sanity:")
    print(f"  usable_w = {usable_w:.2f} in")
    print(f"  slot_pitch = deck_width + slot_clearance = {slot_pitch:.2f} in")
    print(f"  lanes_across = floor(usable_w / slot_pitch) = {la}")

    rd, usable_d, d_left = rows_depth(rack, scooter, c)
    eff_len = max(0.0, scooter.length_in - c.allow_depth_overhang_in)
    row_pitch = eff_len + c.row_clearance_in
    print("\nDepth sanity:")
    print(f"  usable_d = {usable_d:.2f} in")
    print(f"  row_pitch = (scooter_length - overhang) + row_clearance = {row_pitch:.2f} in")
    print(f"  rows_depth = floor(usable_d / row_pitch) capped at {c.max_rows} => {rd}")

    if not results:
        print("\nNo feasible layouts with current inputs.")
        print("Tip: reduce clearances, allow overhang, or verify your rack depth/height.")
        return

    best = results[0]
    print("\nBest layout (by active capacity):")
    print(f"  lanes_across: {best.lanes_across}")
    print(f"  rows_depth:   {best.rows_depth}")
    print(f"  levels:       {best.levels}")
    print(f"  total capacity:  {best.capacity_total}")
    print(f"  active capacity: {best.capacity_active}")
    print(f"  shelf holes: {best.shelf_holes}  (hole_pitch={rack.hole_pitch_in} in)")

    print("\nOrientation suggestion:")
    for row in suggested_orientation(best.rows_depth, best.levels):
        print(f"  {row}")

    print("\nTop 5 feasible layouts:")
    for r in results[:5]:
        print(f"- {r.lanes_across} across × {r.rows_depth} rows × {r.levels} levels"
              f" => total {r.capacity_total}, active {r.capacity_active}, shelves {r.shelf_holes}")

    print("\nIf you WANT 2 rows and/or 2 levels, here are the minimum rack dimensions needed (inside-footprint model):")
    for rows in (1, 2):
        for levels in (1, 2):
            req = requirements_for_target(scooter, c, rows, levels)
            print(f"  rows={rows}, levels={levels}: depth ≥ {req['min_depth_in']:.1f} in, height ≥ {req['min_height_in']:.1f} in")

    print("\nNotes:")
    print("  - If your rack is ~48\" deep and scooters are ~47\" long, you usually only get 1 depth-row inside the posts.")
    print("  - If you expected 6 across at 8.5\" each, 6×8.5=51\" won’t fit in a 48\" bay (unless you allow overhang).")


if __name__ == "__main__":
    main()
