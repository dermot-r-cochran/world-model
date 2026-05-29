"""Developer-facing SDK for building applications on explicit world models and governed world views."""

from __future__ import annotations

from worldeval import ComparabilityDecision, EvaluationResult, EvaluationService
from worldruntime import WorldRuntime
from worldspec import WorldSpec, WorldViewProfile, default_document_world_spec, default_document_worldview_profile


class WorldSDK:
    """High-level SDK that bootstraps world spec, runtime state, and evaluation workflow."""

    def __init__(
        self,
        db_url: str = "sqlite:///./world_framework.db",
        spec: WorldSpec | None = None,
        worldview: WorldViewProfile | None = None,
    ):
        self.spec = spec or default_document_world_spec()
        self.worldview = worldview or default_document_worldview_profile()
        self.runtime = WorldRuntime(self.spec, self.worldview, db_url=db_url)
        self.evaluation = EvaluationService(self.runtime, self.worldview)

    def create_entity(self, stable_id: str, entity_type: str, state: str | None = None, attributes: dict | None = None):
        return self.runtime.create_entity(stable_id=stable_id, entity_type=entity_type, state=state, attributes=attributes)

    def transition(self, stable_id: str, to_state: str, reason: str, evidence_id: str | None = None):
        return self.runtime.transition_entity(stable_id=stable_id, to_state=to_state, reason=reason, evidence_id=evidence_id)

    def attach_evidence(
        self,
        evidence_id: str,
        subject_stable_id: str,
        source_ref: str,
        excerpt: str,
        source_system: str = "system_of_record",
        metadata: dict | None = None,
    ):
        return self.runtime.attach_evidence(
            evidence_id=evidence_id,
            subject_stable_id=subject_stable_id,
            source_ref=source_ref,
            excerpt=excerpt,
            source_system=source_system,
            evidence_metadata=metadata,
        )

    def create_claim(self, claim_id: str, stable_id: str, claim_type: str, payload: dict, evidence_id: str | None):
        return self.runtime.create_claim(
            claim_id=claim_id,
            stable_id=stable_id,
            claim_type=claim_type,
            payload=payload,
            evidence_id=evidence_id,
        )

    def create_relation(self, relation_type: str, source_stable_id: str, target_stable_id: str):
        return self.runtime.create_relation(
            relation_type=relation_type,
            source_stable_id=source_stable_id,
            target_stable_id=target_stable_id,
        )

    def enforce_invariants(self, stable_ids: list[str] | None = None):
        return self.runtime.enforce_invariants(stable_ids=stable_ids)

    def evaluate_run(
        self,
        run_id: str,
        test_set_version: str,
        alignment_strategy: str,
        extracted_rows: list[dict],
        truth_rows: list[dict],
    ) -> EvaluationResult:
        return self.evaluation.evaluate_rows(
            run_id=run_id,
            test_set_version=test_set_version,
            alignment_strategy=alignment_strategy,
            extracted_rows=extracted_rows,
            truth_rows=truth_rows,
        )

    def compare_runs(self, run_a_id: str, run_b_id: str) -> ComparabilityDecision:
        return self.evaluation.compare_runs(run_a_id=run_a_id, run_b_id=run_b_id)

    def world_view(self, stable_id: str) -> dict:
        return self.runtime.world_state(stable_id)
