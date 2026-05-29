# ADR-001: World model is more than retrieval memory

## Decision
Use explicit typed world model artifacts rather than prompt-memory-only patterns.

## Rationale
Business workflows need deterministic state transitions, auditable evidence, and invariant enforcement.

## Consequences
Runtime persists governed records and causal events, enabling reproducibility and correction loops.
