# world-model

Production-minded internal Python framework/SDK for building business AI systems around explicit **world models** and governed **world views**.

## Why this framework exists

Some business AI workflows require durable structure, not stateless prompt inference. This framework provides a small but serious engineering kernel for:

- explicit ontology and identity over time
- state transitions and causal event history
- evidence traceability for claims
- invariant enforcement and violation recording
- evaluation runs and explicit run comparability decisions
- worldview policy as a typed, operational artifact

## World model vs world view

- **World model**: structured, versioned, evidence-linked representation of domain reality (entities, relations, identity rules, state, transitions, invariants, evaluation history).
- **World view**: interpretive and normative policy layer (trust hierarchy, ambiguity policy, comparability policy, accountability mapping, escalation policy).

## ASM / ADM framing

- **ASM** (`worldspec`): semantic and normative specification.
- **ADM** (`worldruntime`): operational realization, enforcement, persistence, and auditable updates.

## Package layout

- `src/worldspec`: ontology, identity rules, state/transition rules, evidence policy, invariants, worldview profile
- `src/worldruntime`: persistence models, command runtime, event log, invariant enforcement, run records
- `src/worldeval`: evaluation and comparability services
- `src/worldsdk`: developer-facing SDK + optional FastAPI API
- `examples/document_extraction`: coherent example app

## Quick start

```bash
cd world-model
python -m pip install -e .[dev]
pytest -q
python examples/document_extraction/run_example.py
uvicorn worldsdk.api:create_app --factory --reload
```

## What first version provides

- durable SQLite-backed runtime
- explicit identity and transition enforcement
- evidence attachment and evidence-required claims
- invariant checks for required evidence classes
- persisted evaluation runs
- explicit comparability decisions across runs

## Out of scope

- distributed runtime and multi-service orchestration
- generic agent framework abstractions
- broad plugin ecosystems
- heavy UI
