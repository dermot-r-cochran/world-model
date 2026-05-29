"""Core runtime engine implementing command-driven world state changes with governance checks."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from sqlmodel import Session, select

from worldspec import WorldSpec, WorldViewProfile

from .errors import EvidenceError, IdentityError, InvariantError, TransitionError
from .storage import (
    ComparabilityDecisionRecord,
    EntityVersion,
    EvaluationRunRecord,
    EvidenceRecord,
    InvariantViolationRecord,
    RelationRecord,
    WorldEvent,
    create_sqlite_engine,
    init_db,
    latest_entity,
    next_entity_version,
)


class WorldRuntime:
    """Operational ADM kernel for persistent state, transitions, events, invariants, and run records."""

    def __init__(self, spec: WorldSpec, worldview: WorldViewProfile, db_url: str = "sqlite:///./world_framework.db"):
        self.spec = spec
        self.worldview = worldview
        self.engine = create_sqlite_engine(db_url)
        init_db(self.engine)

    def create_entity(self, stable_id: str, entity_type: str, state: str | None = None, attributes: dict[str, Any] | None = None) -> EntityVersion:
        """Create new versioned entity while enforcing ontology and identity rules."""

        if not self.spec.has_entity_type(entity_type):
            raise IdentityError(f"Unknown entity type: {entity_type}")

        rule = self.spec.identity_rule_for(entity_type)
        if rule and not stable_id.startswith(rule.required_prefix):
            raise IdentityError(f"stable_id {stable_id!r} must start with {rule.required_prefix!r}")

        state_model = self.spec.state_model_for(entity_type)
        final_state = state or (state_model.initial_state if state_model else "active")

        if state_model and final_state not in state_model.allowed_states:
            raise TransitionError(f"Invalid state {final_state!r} for {entity_type}")

        with Session(self.engine) as session:
            version = next_entity_version(session, stable_id)
            entity = EntityVersion(
                stable_id=stable_id,
                entity_type=entity_type,
                version=version,
                state=final_state,
                attributes=attributes or {},
            )
            session.add(entity)
            session.add(
                WorldEvent(
                    event_type="entity_created",
                    stable_id=stable_id,
                    payload={"entity_type": entity_type, "state": final_state, "version": version},
                )
            )
            session.commit()
            session.refresh(entity)
            return entity

    def attach_evidence(
        self,
        evidence_id: str,
        subject_stable_id: str,
        source_ref: str,
        excerpt: str,
        source_system: str,
        evidence_metadata: dict[str, Any] | None = None,
    ) -> EvidenceRecord:
        """Attach evidence to a stable identity for later traceability and governance."""

        with Session(self.engine) as session:
            subject = latest_entity(session, subject_stable_id)
            if subject is None:
                raise EvidenceError("Evidence subject must exist")

            exists = session.exec(select(EvidenceRecord).where(EvidenceRecord.evidence_id == evidence_id)).first()
            if exists:
                raise EvidenceError(f"Duplicate evidence_id: {evidence_id}")

            record = EvidenceRecord(
                evidence_id=evidence_id,
                subject_stable_id=subject_stable_id,
                source_ref=source_ref,
                excerpt=excerpt,
                source_system=source_system,
                evidence_metadata=evidence_metadata or {},
            )
            session.add(record)
            session.add(
                WorldEvent(
                    event_type="evidence_attached",
                    stable_id=subject_stable_id,
                    evidence_id=evidence_id,
                    payload={"source_ref": source_ref, "source_system": source_system},
                )
            )
            session.commit()
            session.refresh(record)
            return record

    def create_relation(self, relation_type: str, source_stable_id: str, target_stable_id: str) -> RelationRecord:
        """Create typed relation under ontology constraints."""

        with Session(self.engine) as session:
            source = latest_entity(session, source_stable_id)
            target = latest_entity(session, target_stable_id)
            if source is None or target is None:
                raise IdentityError("Relation endpoints must exist")

            if not self.spec.relation_allowed(relation_type, source.entity_type, target.entity_type):
                raise IdentityError(
                    f"Relation {relation_type} not allowed for {source.entity_type}->{target.entity_type}"
                )

            relation = RelationRecord(
                relation_type=relation_type,
                source_stable_id=source_stable_id,
                target_stable_id=target_stable_id,
            )
            session.add(relation)
            session.add(
                WorldEvent(
                    event_type="relation_created",
                    stable_id=source_stable_id,
                    payload={"relation_type": relation_type, "target_stable_id": target_stable_id},
                )
            )
            session.commit()
            session.refresh(relation)
            return relation

    def transition_entity(self, stable_id: str, to_state: str, reason: str, evidence_id: str | None = None) -> EntityVersion:
        """Apply explicit allowed transition and emit transition event."""

        with Session(self.engine) as session:
            current = latest_entity(session, stable_id)
            if current is None:
                raise TransitionError("Cannot transition unknown entity")

            if not self.spec.transition_allowed(current.entity_type, current.state, to_state):
                raise TransitionError(f"Transition not allowed: {current.entity_type} {current.state}->{to_state}")

            if self.spec.evidence_rule.require_evidence_for_transitions and evidence_id is None:
                raise EvidenceError("Transition requires evidence")

            if evidence_id is not None:
                evidence = session.exec(select(EvidenceRecord).where(EvidenceRecord.evidence_id == evidence_id)).first()
                if evidence is None:
                    raise EvidenceError("Transition evidence not found")

            version = next_entity_version(session, stable_id)
            next_state = EntityVersion(
                stable_id=stable_id,
                entity_type=current.entity_type,
                version=version,
                state=to_state,
                attributes=current.attributes,
            )
            session.add(next_state)
            session.add(
                WorldEvent(
                    event_type="state_transition",
                    stable_id=stable_id,
                    evidence_id=evidence_id,
                    payload={"from_state": current.state, "to_state": to_state, "reason": reason},
                )
            )
            session.commit()
            session.refresh(next_state)
            return next_state

    def create_claim(self, claim_id: str, stable_id: str, claim_type: str, payload: dict[str, Any], evidence_id: str | None) -> WorldEvent:
        """Create evidence-backed claim as first-class auditable event."""

        with Session(self.engine) as session:
            subject = latest_entity(session, stable_id)
            if subject is None:
                raise EvidenceError("Claim subject must exist")

            if self.spec.evidence_rule.require_evidence_for_claims and not evidence_id:
                raise EvidenceError("Claims must reference evidence")

            if evidence_id:
                evidence = session.exec(select(EvidenceRecord).where(EvidenceRecord.evidence_id == evidence_id)).first()
                if evidence is None:
                    raise EvidenceError("Claim evidence not found")

            event = WorldEvent(
                event_type="claim_created",
                stable_id=stable_id,
                evidence_id=evidence_id,
                payload={"claim_id": claim_id, "claim_type": claim_type, "payload": payload},
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event

    def enforce_invariants(self, stable_ids: Iterable[str] | None = None) -> list[InvariantViolationRecord]:
        """Evaluate invariant specs and persist violations for governance loops."""

        violations: list[InvariantViolationRecord] = []
        with Session(self.engine) as session:
            target_entities = []
            if stable_ids is None:
                target_entities = session.exec(select(EntityVersion)).all()
            else:
                for stable_id in stable_ids:
                    entity = latest_entity(session, stable_id)
                    if entity:
                        target_entities.append(entity)

            for entity in target_entities:
                if (
                    entity.entity_type in self.spec.evidence_rule.required_evidence_for_entity_types
                    and not session.exec(
                        select(EvidenceRecord).where(EvidenceRecord.subject_stable_id == entity.stable_id)
                    ).first()
                ):
                    violation = InvariantViolationRecord(
                        code="ROW_EVIDENCE_REQUIRED",
                        severity="error",
                        stable_id=entity.stable_id,
                        details={"entity_type": entity.entity_type, "message": "Missing required evidence"},
                    )
                    session.add(violation)
                    violations.append(violation)

            session.commit()
            for violation in violations:
                session.refresh(violation)
            return violations

    def record_evaluation_run(
        self,
        run_id: str,
        test_set_version: str,
        worldview_profile: str,
        alignment_strategy: str,
        metrics: dict[str, Any],
        mismatches: list[dict[str, Any]],
    ) -> EvaluationRunRecord:
        """Persist evaluation outputs for reproducibility and comparability checks."""

        with Session(self.engine) as session:
            existing = session.exec(select(EvaluationRunRecord).where(EvaluationRunRecord.run_id == run_id)).first()
            if existing:
                raise InvariantError(f"run_id already exists: {run_id}")

            run = EvaluationRunRecord(
                run_id=run_id,
                test_set_version=test_set_version,
                worldview_profile=worldview_profile,
                alignment_strategy=alignment_strategy,
                metrics=metrics,
                mismatches=mismatches,
            )
            session.add(run)
            session.add(
                WorldEvent(
                    event_type="evaluation_run_recorded",
                    stable_id=run_id,
                    payload={
                        "test_set_version": test_set_version,
                        "worldview_profile": worldview_profile,
                        "alignment_strategy": alignment_strategy,
                        "metrics": metrics,
                    },
                )
            )
            session.commit()
            session.refresh(run)
            return run

    def get_evaluation_run(self, run_id: str) -> EvaluationRunRecord | None:
        """Fetch one recorded evaluation run."""

        with Session(self.engine) as session:
            return session.exec(select(EvaluationRunRecord).where(EvaluationRunRecord.run_id == run_id)).first()

    def record_comparability_decision(
        self,
        run_a_id: str,
        run_b_id: str,
        decision: str,
        reason_code: str,
        details: dict[str, Any],
    ) -> ComparabilityDecisionRecord:
        """Persist explicit comparability decision between two runs."""

        with Session(self.engine) as session:
            record = ComparabilityDecisionRecord(
                run_a_id=run_a_id,
                run_b_id=run_b_id,
                decision=decision,
                reason_code=reason_code,
                details=details,
            )
            session.add(record)
            session.add(
                WorldEvent(
                    event_type="comparability_decided",
                    stable_id=f"{run_a_id}::{run_b_id}",
                    payload={"decision": decision, "reason_code": reason_code, "details": details},
                )
            )
            session.commit()
            session.refresh(record)
            return record

    def world_state(self, stable_id: str) -> dict[str, Any]:
        """Return latest entity state plus evidence, relations, and event history."""

        with Session(self.engine) as session:
            current = latest_entity(session, stable_id)
            if current is None:
                return {}

            evidence = session.exec(select(EvidenceRecord).where(EvidenceRecord.subject_stable_id == stable_id)).all()
            relations = session.exec(
                select(RelationRecord).where(
                    (RelationRecord.source_stable_id == stable_id) | (RelationRecord.target_stable_id == stable_id)
                )
            ).all()
            events = session.exec(select(WorldEvent).where(WorldEvent.stable_id == stable_id).order_by(WorldEvent.id.asc())).all()
            violations = session.exec(
                select(InvariantViolationRecord).where(InvariantViolationRecord.stable_id == stable_id)
            ).all()

            return {
                "stable_id": stable_id,
                "entity_type": current.entity_type,
                "version": current.version,
                "state": current.state,
                "attributes": current.attributes,
                "worldview_profile": self.worldview.name,
                "evidence": [item.model_dump() for item in evidence],
                "relations": [item.model_dump() for item in relations],
                "events": [item.model_dump() for item in events],
                "violations": [item.model_dump() for item in violations],
            }
