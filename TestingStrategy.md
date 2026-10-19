# Testing Strategy

How this repository is tested, what each tier means, and where the gaps are.

## The governing principle

The framework's value is **durable, governed structure** — world models,
invariants, comparability policies — so the tests are organised by what kind
of confidence each one produces, and the directory layout is the strategy:

- **`tests/unit/`** — one rule, in isolation: the worldview comparability
  policy, spec runtime rules, invariant enforcement, and that every
  comparability decision is persisted (ADR-004). When one of these fails, a
  governance rule changed meaning.
- **`tests/integration/`** — a flow across components: document extraction
  end to end, and state written by one `WorldSDK` read back by a fresh one on
  the same file (the "durable" in the README). When this fails, the pieces
  stopped composing.
- **`tests/regression/`** — pinned incidents: the comparability edge case
  lives here because it once behaved wrongly, and the tier exists so a fixed
  bug cannot return unnoticed. **A bug fix lands with its regression test in
  this directory, in the same change.**

Run: `pytest` (config in `pyproject.toml`: `pythonpath = ["src"]`,
`testpaths = ["tests"]`). All 10 tests verified passing locally on 2026-10-19
with the `dev` extra installed (`pip install -e ".[dev]"`).

## What the tiers deliberately separate

A unit test asserting an invariant and an integration test exercising a flow
fail for different reasons, and mixing them in one directory makes every
failure a research project. The three-tier layout keeps the first question —
"what kind of thing broke?" — answered by the path alone.

## Known gaps (candidates for next)

- ~~No CI~~ — **closed 2026-08-24**: `.github/workflows/ci.yml` runs the
  suite on Python 3.12/3.13 with a coverage ratchet at the measured 86%
  baseline, on every PR and push to `main`.
- **Ten tests is thin for a FastAPI + SQLModel service.** The API surface
  (routing, validation errors, persistence round-trips via `httpx`, which is
  already in the dev extra) has no direct coverage yet; the invariant and
  policy layers are the right ones to deepen first, since they are the
  product.
- ~~Coverage is not measured~~ — the CI ratchet above holds it at ≥87%
  (raised from 86 on 2026-10-19 with the persistence tests, measured 87.73%);
  raise the number in the same change that adds the tests that earn it. Note
  that pytest-cov compares the rounded figure, so a ratchet of N passes from
  N-0.5%: set it at or below the measured whole number, never the rounded one.
- No lint configuration; `ruff` with the repo's conventions would be a
  one-file addition, added green (fix findings in the same change that adds
  the job).
