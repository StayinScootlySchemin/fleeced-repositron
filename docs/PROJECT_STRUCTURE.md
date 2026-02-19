# Project structure and GitHub foundations

This repository is a **single Python package project** (not a monorepo).

## Recommended layout

- `scooter_rack_sim/`: package source
  - `models.py`: input/output datamodels
  - `simulator.py`: feasibility, candidate generation, ranking, jam risk model
  - `cli.py`: command-line entrypoint
- `tests/`: unit tests
- `examples/`: canned user configs
- `docs/`: product/architecture notes
- `.github/`: automation and collaboration templates

## GitHub hygiene

- Use issue templates for bug reports and feature requests.
- Use a PR template to standardize simulator behavior notes and validation commands.
- Add CI to run tests on push and pull requests.

## Versioning suggestion

- Keep package semver in `pyproject.toml`.
- Suggested branch strategy:
  - `main`: stable releasable code
  - short-lived feature branches for each change
