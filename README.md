# fleeced-repositron

Python package `scooter_rack_sim` simulates scooter rack layouts and ranks candidates by:

- Active capacity (higher is better)
- Jam/collision risk from a simple top-view 2-rectangle model (deck + handlebar)

## Is this a project or a repo starter?

This should be treated as a **single focused Python project**. The current structure is intentionally minimal and scalable:

- `scooter_rack_sim/` - core package
- `tests/` - automated checks
- `examples/` - canned JSON configs
- `docs/` - structure and project notes
- `.github/` - CI and issue/PR templates

See `docs/PROJECT_STRUCTURE.md` for a practical GitHub organization guide.

## Install

```bash
python -m pip install -e .
```

## CLI

```bash
scooter-rack-sim --config examples/config_baseline.json --csv output/layouts.csv
```

The CLI prints a build sheet per layout with shelf hole numbers and lane spacing marks, and exports all selected layouts to CSV.

## Config schema

```json
{
  "rack": {"width": 2400, "depth": 700, "height": 1150},
  "hole_pitch": 50,
  "unusable_holes": [5, 6, 28],
  "scooter": {
    "deck_width": 180,
    "deck_length": 620,
    "deck_height": 160,
    "handlebar_width": 520,
    "stem_offset": 110
  },
  "constraints": {
    "side_clearance": 40,
    "front_clearance": 30,
    "rear_clearance": 30,
    "top_clearance": 100,
    "allowed_overhang": 50,
    "access_sides": ["left", "right"],
    "stagger_offsets": [0, 30, 60]
  },
  "top_n": 5
}
```

See `examples/` for additional canned configs.
