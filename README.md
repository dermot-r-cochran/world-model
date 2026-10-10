# world-model

A small Python framework for business AI systems that need **durable, governed
structure** rather than stateless prompt inference — explicit **world models**
and the **world views** that govern how they are interpreted.

---

## Why this exists

A retrieval memory can tell you what was said. It cannot tell you what is
*true now*, how the system got there, what evidence supports it, or whether two
evaluation runs are even comparable.

Business workflows need those answers, and they need them to survive being
audited months later. That means deterministic state transitions, evidence
attached to claims, invariants that are enforced rather than hoped for, and a
record of *why* a decision was made. This framework is the engineering kernel
for that — deliberately small, deliberately opinionated.

**This is not memory, and the distinction is the founding decision** (ADR-001).
Prompt-memory patterns are retrieval; this is governed state with causal
history and correction loops.

## World model vs world view

The split is the central idea, and the two halves answer different questions.

| | Answers | Contains |
|---|---|---|
| **World model** | *What is the case?* | entities, relations, identity rules, state, transitions, invariants, evaluation history — structured, versioned, evidence-linked |
| **World view** | *How should we read it?* | trust hierarchy, ambiguity policy, comparability policy, accountability mapping, escalation policy |

Keeping the normative layer separate and **typed** means policy is an
operational artefact you can version and test, not prose in a wiki that
disagrees with the code (ADR-003).

## ASM / ADM

- **ASM** (`worldspec`) — the semantic and normative *specification*.
- **ADM** (`worldruntime`) — its operational *realisation*: enforcement,
  persistence, auditable updates.

Specification and runtime are separate packages so the first can be reasoned
about without the second.

---

## Three decisions worth knowing before reading the code

Full set in [`docs/decisions/`](docs/decisions/).

**Identity is first-class** (ADR-002). Every governed entity type declares
explicit identity rules and stable IDs, and the runtime enforces identity
prefixes and versioned state per ID. Comparability, lineage and accountability
all collapse without stable identity over time — so it is not left to
convention. Proved by
`tests/unit/test_spec_runtime_rules.py::test_identity_rules_enforced_by_prefix`
and
`tests/regression/test_recreate_cannot_bypass_transitions.py::test_regression_recreating_an_entity_cannot_perform_a_refused_transition`.

**Comparability is explicit** (ADR-004). Comparing two evaluation runs *always*
produces a persisted comparability decision carrying a reason code, checked
against worldview profile, test-set version and alignment strategy. Silent
comparison across incompatible runs is the failure mode this exists to prevent:
it does not error, it just quietly produces a misleading governance outcome.
Proved by
`tests/unit/test_worldview_comparability_policy.py::test_comparability_decision_rejects_alignment_mismatch`
and
`tests/regression/test_comparability_edge_case.py::test_regression_runs_with_different_test_set_versions_not_comparable`;
that the decision is persisted has no test yet.

The alignment strategy is a comparability label, recorded for comparing runs
and not acted on: evaluation always aligns rows by `row_id`, whatever the label
says. That is deliberate while the project is a prototype (decided
2026-10-10).

**Evidence is required, not decorative** (see
[`docs/concepts/invariants-evidence.md`](docs/concepts/invariants-evidence.md)).
Claims can be marked evidence-required, and invariants check for required
evidence classes rather than trusting that someone attached something. Proved
by `tests/unit/test_spec_runtime_rules.py::test_claim_requires_evidence` and
`tests/unit/test_invariant_enforcement.py::test_invariant_requires_evidence_for_extracted_row`.

---

## Package layout

| Package | Role |
|---|---|
| `src/worldspec` | ontology, identity rules, state/transition rules, evidence policy, invariants, worldview profile |
| `src/worldruntime` | persistence models, command runtime, event log, invariant enforcement, run records |
| `src/worldeval` | evaluation and comparability services |
| `src/worldsdk` | developer-facing SDK, plus an optional FastAPI app (the app has no test yet) |
| `examples/document_extraction` | a coherent worked example, end to end |

## Quick start

```bash
python -m pip install -e ".[dev]"
pytest -q
python examples/document_extraction/run_example.py
uvicorn worldsdk.api:create_app --factory --reload
```

The example is the fastest way in: it exercises identity, transitions, evidence
and a comparability decision in one flow.

## Tests

Eight tests, structured by what they protect, not by module:

- `tests/unit` — invariant enforcement, spec/runtime rules, worldview comparability policy
- `tests/integration` — the document-extraction flow end to end
- `tests/regression` — a comparability edge case worth never regressing

---

## What the first version provides

Each line names the test that proves it, or says there is none yet.

- durable SQLite-backed runtime — every test runs on it (in memory);
  persistence across a restart has no test yet
- explicit identity and transition enforcement —
  `tests/unit/test_spec_runtime_rules.py::test_identity_rules_enforced_by_prefix`,
  `tests/unit/test_spec_runtime_rules.py::test_valid_and_invalid_transitions`
- evidence attachment and evidence-required claims —
  `tests/integration/test_document_extraction_flow.py::test_end_to_end_document_extraction_flow`,
  `tests/unit/test_spec_runtime_rules.py::test_claim_requires_evidence`
- invariant checks for required evidence classes —
  `tests/unit/test_invariant_enforcement.py::test_invariant_requires_evidence_for_extracted_row`
- persisted evaluation runs — read back by `compare_runs` in
  `tests/unit/test_worldview_comparability_policy.py::test_comparability_decision_rejects_alignment_mismatch`
- explicit comparability decisions across runs —
  `tests/unit/test_worldview_comparability_policy.py::test_comparability_decision_rejects_alignment_mismatch`,
  `tests/regression/test_comparability_edge_case.py::test_regression_runs_with_different_test_set_versions_not_comparable`

## Out of scope

Named deliberately, so the boundary is visible:

- distributed runtime and multi-service orchestration
- generic agent-framework abstractions
- broad plugin ecosystems
- heavy UI

## Status

Research prototype. The concepts and decisions are settled and documented in
[`docs/`](docs/); interfaces may still change.

## Licence

MIT — see [LICENSE](LICENSE).
