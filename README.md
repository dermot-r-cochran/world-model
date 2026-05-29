# world-model

Production-minded Python proof-of-concept for an explicit **world view platform** and **framework SDK** for business AI workflows.

## What this repository provides

- A **WorldViewSDK** for creating and evolving explicit world state.
- A **FastAPI platform service** exposing world-view commands and queries.
- SQLite-backed persistence for entities, relations, evidence, and event history.
- Invariant enforcement for ontology, transitions, and evidence requirements.

## World view definition

A **world view** is the system's coherent interpretation of reality, defined by:

- ontology
- state
- causal assumptions
- evidence rules
- invariants

In ASM/ADM terms:

- **ASM** specifies this semantic structure.
- **ADM** ensures it is instantiated, enforced, and revised in runtime operation.

## Quick start

```bash
cd /tmp/workspace/UL-AIL/world-model
python -m pip install -e .[dev]
pytest -q
python scripts/run_demo.py
uvicorn worldview.api:create_app --factory --reload
```

## Core API endpoints

- `POST /entities` — create versioned entity state with stable identity
- `POST /relations` — create typed relations under ontology constraints
- `POST /evidence` — register traceable source evidence
- `POST /transitions` — apply ASM-constrained state transitions
- `POST /claims` — create claims with mandatory evidence linkage
- `GET /world-view/{stable_id}` — retrieve current state + evidence + causal log

## Notes

This POC intentionally stays small in scope while keeping explicit semantics and enforcement suitable as a seed for a larger internal framework.
