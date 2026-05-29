"""Persistence models and helpers for world runtime state and governance records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select


class EntityVersion(SQLModel, table=True):
    """Versioned world entity state with stable identity."""

    id: int | None = Field(default=None, primary_key=True)
    stable_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    version: int = Field(index=True)
    state: str
    attributes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class RelationRecord(SQLModel, table=True):
    """Persisted relation between stable identities."""

    id: int | None = Field(default=None, primary_key=True)
    relation_type: str = Field(index=True)
    source_stable_id: str = Field(index=True)
    target_stable_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvidenceRecord(SQLModel, table=True):
    """Evidence object grounding a subject identity to source context."""

    id: int | None = Field(default=None, primary_key=True)
    evidence_id: str = Field(unique=True, index=True)
    subject_stable_id: str = Field(index=True)
    source_ref: str
    excerpt: str
    source_system: str
    evidence_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorldEvent(SQLModel, table=True):
    """Immutable event log for auditable causal traceability."""

    id: int | None = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    stable_id: str | None = Field(default=None, index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    evidence_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvariantViolationRecord(SQLModel, table=True):
    """Persisted invariant violation for governance and correction loops."""

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    severity: str
    stable_id: str | None = Field(default=None, index=True)
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvaluationRunRecord(SQLModel, table=True):
    """Evaluation run metadata and results for reproducibility and comparison."""

    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(unique=True, index=True)
    test_set_version: str = Field(index=True)
    worldview_profile: str = Field(index=True)
    alignment_strategy: str
    metrics: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    mismatches: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ComparabilityDecisionRecord(SQLModel, table=True):
    """Stored comparability decision between two evaluation runs."""

    id: int | None = Field(default=None, primary_key=True)
    run_a_id: str = Field(index=True)
    run_b_id: str = Field(index=True)
    decision: str = Field(index=True)
    reason_code: str
    details: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def create_sqlite_engine(url: str = "sqlite:///./world_framework.db"):
    """Create SQLite engine for file or in-memory usage."""

    if url == "sqlite://":
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, echo=False)


def init_db(engine) -> None:
    """Create runtime schema tables."""

    SQLModel.metadata.create_all(engine)


def next_entity_version(session: Session, stable_id: str) -> int:
    """Return next monotonically increasing version for stable identity."""

    latest = session.exec(
        select(EntityVersion)
        .where(EntityVersion.stable_id == stable_id)
        .order_by(EntityVersion.version.desc())
    ).first()
    return 1 if latest is None else latest.version + 1


def latest_entity(session: Session, stable_id: str) -> EntityVersion | None:
    """Fetch latest entity version for stable identity."""

    return session.exec(
        select(EntityVersion)
        .where(EntityVersion.stable_id == stable_id)
        .order_by(EntityVersion.version.desc())
    ).first()
