# Evaluation and comparability

Evaluation runs are persisted with:
- run ID
- test set version
- worldview profile
- alignment strategy
- metrics and mismatches

The alignment strategy is a label, not a behaviour. It is recorded so that
`compare_runs` can refuse to compare two runs made under different strategies;
nothing acts on it, and evaluation always aligns rows by `row_id` whatever the
label says. That is deliberate while the project is a prototype (decided
2026-10-10).

Comparability is explicit, not implicit.

`compare_runs` yields a typed decision:
- `comparable`
- `not_comparable`

with reason codes like:
- `ALIGNMENT_STRATEGY_MISMATCH`
- `TEST_SET_VERSION_MISMATCH`
- `WORLDVIEW_PROFILE_MISMATCH`
