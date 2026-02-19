from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RackDimensions:
    width: float
    depth: float
    height: float


@dataclass(frozen=True)
class ScooterGeometry:
    deck_width: float
    deck_length: float
    deck_height: float
    handlebar_width: float
    stem_offset: float


@dataclass(frozen=True)
class Constraints:
    side_clearance: float
    front_clearance: float
    rear_clearance: float
    top_clearance: float
    allowed_overhang: float
    access_sides: tuple[str, ...]
    stagger_offsets: tuple[float, ...]


@dataclass(frozen=True)
class Config:
    rack: RackDimensions
    hole_pitch: float
    unusable_holes: tuple[int, ...]
    scooter: ScooterGeometry
    constraints: Constraints
    top_n: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Config":
        rack_data = data["rack"]
        scooter_data = data["scooter"]
        constraints_data = data["constraints"]

        return cls(
            rack=RackDimensions(
                width=float(rack_data["width"]),
                depth=float(rack_data["depth"]),
                height=float(rack_data["height"]),
            ),
            hole_pitch=float(data["hole_pitch"]),
            unusable_holes=tuple(sorted(int(i) for i in data.get("unusable_holes", []))),
            scooter=ScooterGeometry(
                deck_width=float(scooter_data["deck_width"]),
                deck_length=float(scooter_data["deck_length"]),
                deck_height=float(scooter_data["deck_height"]),
                handlebar_width=float(scooter_data["handlebar_width"]),
                stem_offset=float(scooter_data.get("stem_offset", 0.0)),
            ),
            constraints=Constraints(
                side_clearance=float(constraints_data.get("side_clearance", 0.0)),
                front_clearance=float(constraints_data.get("front_clearance", 0.0)),
                rear_clearance=float(constraints_data.get("rear_clearance", 0.0)),
                top_clearance=float(constraints_data.get("top_clearance", 0.0)),
                allowed_overhang=float(constraints_data.get("allowed_overhang", 0.0)),
                access_sides=tuple(constraints_data.get("access_sides", ["left", "right"])),
                stagger_offsets=tuple(float(v) for v in constraints_data.get("stagger_offsets", [0.0])),
            ),
            top_n=int(data.get("top_n", 5)),
        )


@dataclass(frozen=True)
class LanePlacement:
    hole: int
    center_x: float
    stagger_offset: float


@dataclass(frozen=True)
class LayoutResult:
    layout_id: int
    active_capacity: int
    jam_risk: float
    lane_spacing: float
    stagger_offset: float
    holes: tuple[int, ...]
    feasibility_notes: tuple[str, ...]
