# AGENTS.md
## Overview
This repo ingests large ChatGPT exports, builds a pgvector index, and exposes domain agents (Braki, Quarti, Fiski).

## Rules for Codex
1. Use Python 3.11, Poetry for deps.
2. All vector code lives under `scripts/`.
3. When adding a new agent, create a folder under `agents/` and a pytest file.
4. Pass `ruff` and `pytest -q` before proposing a PR.

## Commands
- ruff check .
- pytest -q
