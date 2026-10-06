# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -e ".[dev]"        # install (Python >= 3.12; dev extra adds pytest, pytest-cov, httpx)
pytest                          # run the whole suite (config in pyproject.toml: pythonpath=["src"], testpaths=["tests"])
pytest tests/unit/test_invariant_enforcement.py            # one file
pytest tests/unit/test_invariant_enforcement.py::test_name # one test
pytest --cov=src --cov-fail-under=86                       # what CI runs (Python 3.12 and 3.13)
python examples/document_extraction/run_example.py         # the end-to-end worked example
uvicorn worldsdk.api:create_app --factory --reload         # optional FastAPI app
```

There is no lint or typecheck configuration yet (`TestingStrategy.md` lists `ruff` as a known gap). The CI coverage number is a ratchet at the measured baseline: raise it with the tests that earn it, never lower it.

## What this is

A small, deliberately opinionated framework for business AI systems that need **durable, governed structure** instead of stateless prompt inference: explicit **world models** (*what is the case* — typed entities, stable identities, versioned state, transitions, evidence-linked claims, invariants) and **world views** (*how should we read it* — a typed `WorldViewProfile` carrying trust hierarchy, ambiguity, comparability, escalation and accountability policy). This is **not memory** — retrieval tells you what was said; this is governed state with causal history and correction loops (ADR-001).

## Architecture

Four packages under `src/`, split on the ASM/ADM axis (`docs/concepts/asm-adm.md`):

- **`worldspec`** — the ASM: the semantic/normative *specification*. Pydantic contracts for ontology, identity rules, state/transition rules, evidence policy, invariants, and `WorldViewProfile`. Pure declaration — reasoned about without the runtime.
- **`worldruntime`** — the ADM: the specification's operational *realisation*. `WorldRuntime` takes a `WorldSpec` + `WorldViewProfile` and enforces them over SQLite/SQLModel persistence: versioned entity state, transition and identity enforcement, evidence attachment, event log, invariant-violation records.
- **`worldeval`** — evaluation on top of the runtime. `EvaluationService` persists evaluation runs (run ID, test-set version, worldview profile, alignment strategy) and implements explicit comparability: `compare_runs` always yields a persisted, typed decision with a reason code (e.g. `TEST_SET_VERSION_MISMATCH`), never a silent comparison.
- **`worldsdk`** — developer-facing composition: `WorldSDK` bootstraps spec + runtime + evaluation with defaults, plus the optional FastAPI app (`worldsdk.api`).

`examples/document_extraction/` exercises identity, transitions, evidence, invariants and a comparability decision in one flow — the fastest way into the codebase.

## The decisions that shape the code

`docs/decisions/` holds ADRs 001–004; they explain most non-obvious design choices, so read them before changing what they settled:

- **ADR-001** — a world model is more than retrieval memory: typed artifacts, deterministic transitions, auditable evidence.
- **ADR-002** — identity is first-class: every governed entity type declares identity rules and stable IDs; the runtime enforces prefixes and versions state per ID.
- **ADR-003** — worldview policy is typed and operational (`WorldViewProfile`), enforced at runtime/evaluation, never docs-only prose.
- **ADR-004** — comparability decisions are explicit and persisted with reason codes; the failure mode they prevent is a silent, misleading cross-run comparison.

Related: evidence is required, not decorative — claims can be evidence-required and invariants check for required evidence classes (`docs/concepts/invariants-evidence.md`).

## Testing

`TestingStrategy.md` is the authority on mechanics and gaps. The layout **is** the strategy — tiers are organised by what they protect, not by module: `tests/unit/` (one governance rule in isolation), `tests/integration/` (the document-extraction flow composing), `tests/regression/` (pinned incidents — **a bug fix lands with its regression test in that directory, in the same change**).

## Related repositories

The map of Dermot's public repositories and what crosses between them is
`RELATED-REPOSITORIES.md` in `dermot-r-cochran/star-rangers`; this section
names only this repository's own neighbours (added 2026-09-29 at his
direction). Nothing below shares code or data with this repository; what is
shared is stated exactly.

- **`dermot-r-cochran/careful-memory`** is the account's long-term memory
  system for agents, which is exactly what ADR-001 says this repository is
  not: retrieval tells you what was said, this is governed state with causal
  history. The two draw one boundary from opposite sides and share nothing
  else.
- **`dermot-r-cochran/swarm`** (EPISTEME) keeps evidence-linked, revisable
  beliefs as the primitive; this repository keeps evidence-linked claims
  inside a typed world model. Neighbouring ideas, independent code.
- **`dermot-r-cochran/virtual-anthropology`** (The Archipelago) keeps the
  same discipline for a simulated civilisation: canonical state changed only
  by recorded, hash-chained events, replayed and invariant-checked after
  every command, with a research layer that publishes only what traces to
  the log. Independent code; neither imports the other (added 2026-10-01).
- **Siblings by convention:** `careful-memory`, `world-model`, `foundation-model`,
  `shadow-architect`, `visual-llm`, `swarm`, `Voting` and
  `architecture-definition-model` all carry a `TestingStrategy.md` that keeps
  testing mechanics apart from the repository's rules; six run CI coverage as a
  ratchet at the measured baseline (`swarm`, `careful-memory`, `world-model`,
  `foundation-model`, `shadow-architect`, `visual-llm`); five keep
  architecture decision records (`swarm`, `careful-memory`, `world-model`,
  `shadow-architect`, the ADM); `swarm` guards three of its four with a named
  test, `shadow-architect` guards one, and the others say in their own
  `CLAUDE.md` how far tests reach their decisions; here the unit and
  regression tests exercise ADRs 001–004, though no test is named as an
  ADR's guard. When a
  convention here needs changing, those are the reference for how it is done
  in the account, and a change to the convention itself is worth landing in
  all of them or in none.
