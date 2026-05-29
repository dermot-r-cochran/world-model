"""Typed evaluation and comparability models used by evaluation runtime and SDK."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Mismatch(BaseModel):
    """One mismatch between extracted and truth rows with accountability metadata."""

    row_id: str
    mismatch_class: str
    field_name: str
    expected: str | None
    actual: str | None
    owner_team: str


class EvaluationResult(BaseModel):
    """Evaluation run output with metrics and mismatch list."""

    run_id: str
    test_set_version: str
    worldview_profile: str
    alignment_strategy: str
    metrics: dict[str, float] = Field(default_factory=dict)
    mismatches: list[Mismatch] = Field(default_factory=list)


class ComparabilityDecision(BaseModel):
    """Explicit comparability decision for two evaluation runs."""

    run_a_id: str
    run_b_id: str
    decision: str
    reason_code: str
    details: dict = Field(default_factory=dict)
