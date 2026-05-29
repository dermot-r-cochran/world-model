"""Evaluation service implementing reproducible scoring and explicit comparability logic."""

from __future__ import annotations

from worldruntime import WorldRuntime
from worldspec import WorldViewProfile

from .models import ComparabilityDecision, EvaluationResult, Mismatch


class EvaluationService:
    """Runs evaluation and comparability policies against persisted runtime metadata."""

    def __init__(self, runtime: WorldRuntime, worldview: WorldViewProfile):
        self.runtime = runtime
        self.worldview = worldview

    def evaluate_rows(
        self,
        run_id: str,
        test_set_version: str,
        alignment_strategy: str,
        extracted_rows: list[dict],
        truth_rows: list[dict],
    ) -> EvaluationResult:
        """Evaluate extracted rows against truth rows using explicit ID alignment."""

        truth_by_id = {row["row_id"]: row for row in truth_rows}
        mismatches: list[Mismatch] = []
        matches = 0

        for extracted in extracted_rows:
            row_id = extracted["row_id"]
            truth = truth_by_id.get(row_id)
            if truth is None:
                mismatch_class = "missing_truth_row"
                mismatches.append(
                    Mismatch(
                        row_id=row_id,
                        mismatch_class=mismatch_class,
                        field_name="row_id",
                        expected="existing truth row",
                        actual="missing",
                        owner_team=self.worldview.accountability.owner_by_class.get(
                            mismatch_class,
                            "team:world-governance",
                        ),
                    )
                )
                continue

            if truth.get("value") == extracted.get("value"):
                matches += 1
            else:
                mismatch_class = "value_mismatch"
                mismatches.append(
                    Mismatch(
                        row_id=row_id,
                        mismatch_class=mismatch_class,
                        field_name="value",
                        expected=str(truth.get("value")),
                        actual=str(extracted.get("value")),
                        owner_team=self.worldview.accountability.owner_by_class.get(
                            mismatch_class,
                            "team:world-governance",
                        ),
                    )
                )

        total = max(len(truth_rows), 1)
        precision = matches / max(len(extracted_rows), 1)
        recall = matches / total
        metrics = {
            "matched_rows": float(matches),
            "precision": precision,
            "recall": recall,
            "mismatch_count": float(len(mismatches)),
        }

        result = EvaluationResult(
            run_id=run_id,
            test_set_version=test_set_version,
            worldview_profile=self.worldview.name,
            alignment_strategy=alignment_strategy,
            metrics=metrics,
            mismatches=mismatches,
        )

        self.runtime.record_evaluation_run(
            run_id=run_id,
            test_set_version=test_set_version,
            worldview_profile=self.worldview.name,
            alignment_strategy=alignment_strategy,
            metrics=result.metrics,
            mismatches=[m.model_dump() for m in result.mismatches],
        )
        return result

    def compare_runs(self, run_a_id: str, run_b_id: str) -> ComparabilityDecision:
        """Make explicit comparability decision using worldview comparability policy."""

        run_a = self.runtime.get_evaluation_run(run_a_id)
        run_b = self.runtime.get_evaluation_run(run_b_id)
        if run_a is None or run_b is None:
            decision = ComparabilityDecision(
                run_a_id=run_a_id,
                run_b_id=run_b_id,
                decision="not_comparable",
                reason_code="RUN_NOT_FOUND",
                details={},
            )
            self.runtime.record_comparability_decision(
                run_a_id=run_a_id,
                run_b_id=run_b_id,
                decision=decision.decision,
                reason_code=decision.reason_code,
                details=decision.details,
            )
            return decision

        policy = self.worldview.comparability_policy

        if policy.require_same_worldview_profile and run_a.worldview_profile != run_b.worldview_profile:
            reason = "WORLDVIEW_PROFILE_MISMATCH"
            decision = "not_comparable"
        elif policy.require_same_test_set_version and run_a.test_set_version != run_b.test_set_version:
            reason = "TEST_SET_VERSION_MISMATCH"
            decision = "not_comparable"
        elif policy.require_same_alignment_strategy and run_a.alignment_strategy != run_b.alignment_strategy:
            reason = "ALIGNMENT_STRATEGY_MISMATCH"
            decision = "not_comparable"
        else:
            reason = "COMPARABLE"
            decision = "comparable"

        result = ComparabilityDecision(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            decision=decision,
            reason_code=reason,
            details={
                "run_a_alignment": run_a.alignment_strategy,
                "run_b_alignment": run_b.alignment_strategy,
                "test_set_version_a": run_a.test_set_version,
                "test_set_version_b": run_b.test_set_version,
            },
        )
        self.runtime.record_comparability_decision(
            run_a_id=run_a_id,
            run_b_id=run_b_id,
            decision=result.decision,
            reason_code=result.reason_code,
            details=result.details,
        )
        return result
