"""ADM persistence layer using SQLModel and SQLite."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, JSON
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine, select


class EntityRecord(SQLModel, table=True):
    """Versioned entity state with stable identity for world persistence."""

    id: int | None = Field(default=None, primary_key=True)
    stable_id: str = Field(index=True)
    entity_type: str = Field(index=True)
    version: int = Field(index=True)
    state: str
    attributes: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RelationRecord(SQLModel, table=True):
    """Typed relation between stable identities."""

    id: int | None = Field(default=None, primary_key=True)
    relation_type: str = Field(index=True)
    source_stable_id: str = Field(index=True)
    target_stable_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EvidenceRecord(SQLModel, table=True):
    """Evidence artifacts that ground claims and outputs."""

    id: int | None = Field(default=None, primary_key=True)
    evidence_id: str = Field(unique=True, index=True)
    subject_stable_id: str = Field(index=True)
    source_ref: str
    excerpt: str
    evidence_metadata: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EventRecord(SQLModel, table=True):
    """Auditable event log of causal updates and transitions."""

    id: int | None = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    stable_id: str | None = Field(default=None, index=True)
    payload: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    evidence_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def create_sqlite_engine(url: str = "sqlite:///./worldview.db"):
    """Create SQLite engine suitable for local platform and SDK usage."""

    if url == "sqlite://":
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, echo=False)


def init_db(engine) -> None:
    """Initialize all world view persistence tables."""

    SQLModel.metadata.create_all(engine)


def next_entity_version(session: Session, stable_id: str) -> int:
    """Compute next monotonic version for a stable identity."""

    latest = session.exec(
        select(EntityRecord)
        .where(EntityRecord.stable_id == stable_id)
        .order_by(EntityRecord.version.desc())
    ).first()
    return (latest.version + 1) if latest else 1


def latest_entity(session: Session, stable_id: str) -> EntityRecord | None:
    """Get latest versioned entity record by stable identity."""

    return session.exec(
        select(EntityRecord)
        .where(EntityRecord.stable_id == stable_id)
        .order_by(EntityRecord.version.desc())
    ).first()
