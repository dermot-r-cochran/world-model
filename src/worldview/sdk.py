"""Python SDK implementing world view platform semantics and invariant enforcement."""

from __future__ import annotations

from sqlmodel import Session, select

from .asm import WorldASM, default_business_asm
from .domain import ClaimCreate, EntityCreate, EvidenceCreate, RelationCreate, TransitionCommand
from .errors import EvidenceViolation, OntologyViolation, TransitionViolation
from .storage import (
    EntityRecord,
    EventRecord,
    EvidenceRecord,
    RelationRecord,
    create_sqlite_engine,
    init_db,
    latest_entity,
    next_entity_version,
)


class WorldViewSDK:
    """Main SDK entrypoint for managing explicit world view state and semantics."""

    def __init__(self, db_url: str = "sqlite:///./worldview.db", asm: WorldASM | None = None):
        self.asm = asm or default_business_asm()
        self.engine = create_sqlite_engine(db_url)
        init_db(self.engine)

    def create_entity(self, command: EntityCreate) -> EntityRecord:
        """Create new versioned entity state under stable identity."""

        if not self.asm.is_known_entity_type(command.entity_type):
            raise OntologyViolation(f"Unknown entity type: {command.entity_type}")

        with Session(self.engine) as session:
            version = next_entity_version(session, command.stable_id)
            record = EntityRecord(
                stable_id=command.stable_id,
                entity_type=command.entity_type,
                version=version,
                state=command.state,
                attributes=command.attributes,
            )
            session.add(record)
            session.add(
                EventRecord(
                    event_type="entity_created",
                    stable_id=command.stable_id,
                    payload={"entity_type": command.entity_type, "version": version, "state": command.state},
                )
            )
            session.commit()
            session.refresh(record)
            return record

    def create_relation(self, command: RelationCreate) -> RelationRecord:
        """Create relation after ontology and existence checks."""

        with Session(self.engine) as session:
            source = latest_entity(session, command.source_stable_id)
            target = latest_entity(session, command.target_stable_id)
            if not source or not target:
                raise OntologyViolation("Relation endpoints must both exist")
            if not self.asm.is_allowed_relation(command.relation_type, source.entity_type, target.entity_type):
                raise OntologyViolation(
                    f"Disallowed relation: {command.relation_type}({source.entity_type}->{target.entity_type})"
                )

            rel = RelationRecord(
                relation_type=command.relation_type,
                source_stable_id=command.source_stable_id,
                target_stable_id=command.target_stable_id,
            )
            session.add(rel)
            session.add(
                EventRecord(
                    event_type="relation_created",
                    stable_id=command.source_stable_id,
                    payload={
                        "relation_type": command.relation_type,
                        "target_stable_id": command.target_stable_id,
                    },
                )
            )
            session.commit()
            session.refresh(rel)
            return rel

    def add_evidence(self, command: EvidenceCreate) -> EvidenceRecord:
        """Persist evidence grounding and ensure subject identity exists."""

        with Session(self.engine) as session:
            subject = latest_entity(session, command.subject_stable_id)
            if not subject:
                raise EvidenceViolation("Evidence subject must reference an existing entity")

            existing = session.exec(
                select(EvidenceRecord).where(EvidenceRecord.evidence_id == command.evidence_id)
            ).first()
            if existing:
                raise EvidenceViolation(f"Duplicate evidence_id: {command.evidence_id}")

            ev = EvidenceRecord(
                evidence_id=command.evidence_id,
                subject_stable_id=command.subject_stable_id,
                source_ref=command.source_ref,
                excerpt=command.excerpt,
                evidence_metadata=command.metadata,
            )
            session.add(ev)
            session.add(
                EventRecord(
                    event_type="evidence_added",
                    stable_id=command.subject_stable_id,
                    evidence_id=command.evidence_id,
                    payload={"source_ref": command.source_ref},
                )
            )
            session.commit()
            session.refresh(ev)
            return ev

    def apply_transition(self, command: TransitionCommand) -> EntityRecord:
        """Apply explicit state transition constrained by ASM rules."""

        with Session(self.engine) as session:
            current = latest_entity(session, command.stable_id)
            if not current:
                raise TransitionViolation("Cannot transition unknown entity")

            if not self.asm.is_allowed_transition(current.entity_type, current.state, command.to_state):
                raise TransitionViolation(
                    f"Disallowed transition for {current.entity_type}: {current.state}->{command.to_state}"
                )

            if self.asm.require_evidence_for_claims and command.evidence_id:
                evidence = session.exec(
                    select(EvidenceRecord).where(EvidenceRecord.evidence_id == command.evidence_id)
                ).first()
                if not evidence:
                    raise EvidenceViolation("Transition evidence_id not found")

            version = next_entity_version(session, command.stable_id)
            next_record = EntityRecord(
                stable_id=current.stable_id,
                entity_type=current.entity_type,
                version=version,
                state=command.to_state,
                attributes=current.attributes,
            )
            session.add(next_record)
            session.add(
                EventRecord(
                    event_type="state_transition",
                    stable_id=command.stable_id,
                    evidence_id=command.evidence_id,
                    payload={
                        "from_state": current.state,
                        "to_state": command.to_state,
                        "reason": command.reason,
                    },
                )
            )
            session.commit()
            session.refresh(next_record)
            return next_record

    def create_claim(self, command: ClaimCreate) -> EventRecord:
        """Create claim event with mandatory evidence if policy requires it."""

        with Session(self.engine) as session:
            subject = latest_entity(session, command.stable_id)
            if not subject:
                raise EvidenceViolation("Claim subject must exist")

            if self.asm.require_evidence_for_claims and not command.evidence_id:
                raise EvidenceViolation("Claims must reference evidence_id")

            if command.evidence_id:
                evidence = session.exec(
                    select(EvidenceRecord).where(EvidenceRecord.evidence_id == command.evidence_id)
                ).first()
                if not evidence:
                    raise EvidenceViolation("Claim evidence_id not found")

            event = EventRecord(
                event_type="claim_created",
                stable_id=command.stable_id,
                evidence_id=command.evidence_id,
                payload={
                    "claim_id": command.claim_id,
                    "claim_type": command.claim_type,
                    "payload": command.payload,
                },
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def world_view(self, stable_id: str) -> dict:
        """Return current state plus causal/evidence context for one stable identity."""

        with Session(self.engine) as session:
            current = latest_entity(session, stable_id)
            if not current:
                return {}

            evidence = session.exec(
                select(EvidenceRecord).where(EvidenceRecord.subject_stable_id == stable_id)
            ).all()
            events = session.exec(
                select(EventRecord).where(EventRecord.stable_id == stable_id).order_by(EventRecord.id.asc())
            ).all()
            relations = session.exec(
                select(RelationRecord).where(
                    (RelationRecord.source_stable_id == stable_id) | (RelationRecord.target_stable_id == stable_id)
                )
            ).all()

            return {
                "stable_id": stable_id,
                "entity_type": current.entity_type,
                "current_version": current.version,
                "state": current.state,
                "attributes": current.attributes,
                "evidence": [e.model_dump() for e in evidence],
                "relations": [r.model_dump() for r in relations],
                "events": [e.model_dump() for e in events],
            }
