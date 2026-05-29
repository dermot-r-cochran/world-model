# Overview

This repository is a framework seed for business AI systems that must reason over explicit externalized world structure.

The architecture is intentionally small and explicit:

- `worldspec` defines ASM semantics (what the world means and what is allowed).
- `worldruntime` enforces ADM behavior (how state is persisted, updated, and governed).
- `worldeval` records evaluation behavior and comparability decisions.
- `worldsdk` offers application-facing composition and APIs.

The included document extraction example demonstrates identity, evidence grounding, invariant checks, evaluation runs, and explicit comparability outcomes.
