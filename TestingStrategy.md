# Testing Strategy

How this repository is tested, what each tier means, and where the gaps are.

## The governing principle

The framework's value is **durable, governed structure** — world models,
invariants, comparability policies — so the tests are organised by what kind
of confidence each one produces, and the directory layout is the strategy:

- **`tests/unit/`** — one rule, in isolation: the worldview comparability
  policy, spec runtime rules, and invariant enforcement. When one of these
  fails, a governance rule changed meaning.
- **`tests/integration/`** — a flow across components: document extraction
  end to end. When this fails, the pieces stopped composing.
- **`tests/regression/`** — pinned incidents: the comparability edge case
  lives here because it once behaved wrongly, and the tier exists so a fixed
  bug cannot return unnoticed. **A bug fix lands with its regression test in
  this directory, in the same change.**

Run: `pytest` (config in `pyproject.toml`: `pythonpath = ["src"]`,
`testpaths = ["tests"]`). All 7 tests verified passing locally on 2026-08-24
with the `dev` extra installed (`pip install -e ".[dev]"`).

## What the tiers deliberately separate

A unit test asserting an invariant and an integration test exercising a flow
fail for different reasons, and mixing them in one directory makes every
failure a research project. The three-tier layout keeps the first question —
"what kind of thing broke?" — answered by the path alone.

## Known gaps (candidates for next)

- **No CI.** This is the largest gap by far: the suite only runs when someone
  types `pytest`. The sibling `swarm` repo's workflow (pytest on a version
  matrix, `fail-fast: false`, later a coverage ratchet) is the pattern to
  copy; the suite is fast and its dependencies are pip-installable, so the
  workflow is small.
- **Seven tests is thin for a FastAPI + SQLModel service.** The API surface
  (routing, validation errors, persistence round-trips via `httpx`, which is
  already in the dev extra) has no direct coverage yet; the invariant and
  policy layers are the right ones to deepen first, since they are the
  product.
- Coverage is not measured; once CI exists, a `--cov-fail-under` ratchet at
  the measured baseline keeps it from silently falling.
- No lint configuration; `ruff` with the repo's conventions would be a
  one-file addition, added green (fix findings in the same change that adds
  the job).
