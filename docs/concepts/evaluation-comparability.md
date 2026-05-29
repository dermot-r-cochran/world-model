# Evaluation and comparability

Evaluation runs are persisted with:
- run ID
- test set version
- worldview profile
- alignment strategy
- metrics and mismatches

Comparability is explicit, not implicit.

`compare_runs` yields a typed decision:
- `comparable`
- `not_comparable`

with reason codes like:
- `ALIGNMENT_STRATEGY_MISMATCH`
- `TEST_SET_VERSION_MISMATCH`
- `WORLDVIEW_PROFILE_MISMATCH`
