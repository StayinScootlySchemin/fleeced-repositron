# Contributing

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install pytest
```

## Run checks

```bash
python -m pytest -q
python -m scooter_rack_sim.cli --config examples/config_baseline.json --csv layouts.csv
```

## Pull requests

- Keep changes scoped and include tests for behavior changes.
- Update README/docs when config schema or output format changes.
- Prefer additive changes to config schema to maintain compatibility.
