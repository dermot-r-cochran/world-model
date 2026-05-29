"""Pydantic contracts that define explicit world view semantics for SDK and API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EntityCreate(BaseModel):
    """Command to create or update versioned entity state with stable identity."""

    stable_id: str
    entity_type: str
    state: str
    attributes: dict = Field(default_factory=dict)


class RelationCreate(BaseModel):
    """Command to create a typed relation between two entities."""

    relation_type: str
    source_stable_id: str
    target_stable_id: str


class EvidenceCreate(BaseModel):
    """Evidence object anchoring a claim to a source location."""

    evidence_id: str
    subject_stable_id: str
    source_ref: str
    excerpt: str
    metadata: dict = Field(default_factory=dict)


class TransitionCommand(BaseModel):
    """Command for explicit state transition based on ASM rules."""

    stable_id: str
    to_state: str
    reason: str
    evidence_id: str | None = None


class ClaimCreate(BaseModel):
    """Claim event requiring traceable evidence when configured by ASM."""

    claim_id: str
    stable_id: str
    claim_type: str
    payload: dict = Field(default_factory=dict)
    evidence_id: str | None = None
