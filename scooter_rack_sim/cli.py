from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .models import Config
from .simulator import build_sheet, simulate_layouts


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scooter rack layout simulator")
    parser.add_argument("--config", required=True, help="Path to JSON config")
    parser.add_argument("--csv", default="layouts.csv", help="Output CSV path")
    return parser.parse_args()


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "layout_id",
        "active_capacity",
        "jam_risk",
        "lane_spacing",
        "stagger_offset",
        "holes",
        "feasibility_notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = _parse_args()
    config_path = Path(args.config)
    output_csv = Path(args.csv)

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    config = Config.from_dict(raw)
    layouts = simulate_layouts(config)

    if not layouts:
        print("No layouts found.")
        return

    for layout in layouts:
        print(build_sheet(layout, config))
        print("-" * 60)

    rows = [
        {
            "layout_id": l.layout_id,
            "active_capacity": l.active_capacity,
            "jam_risk": l.jam_risk,
            "lane_spacing": l.lane_spacing,
            "stagger_offset": l.stagger_offset,
            "holes": " ".join(str(h) for h in l.holes),
            "feasibility_notes": " | ".join(l.feasibility_notes),
        }
        for l in layouts
    ]
    _write_csv(output_csv, rows)
    print(f"Exported CSV: {output_csv}")


if __name__ == "__main__":
    main()
