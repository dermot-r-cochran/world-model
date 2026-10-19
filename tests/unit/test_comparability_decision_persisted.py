from sqlmodel import Session, select

from worldruntime import ComparabilityDecisionRecord, WorldEvent
from worldsdk import WorldSDK


def _evaluate(sdk: WorldSDK, run_id: str, test_set_version: str) -> None:
    sdk.evaluate_run(
        run_id=run_id,
        test_set_version=test_set_version,
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:1", "value": "10"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )


def test_every_comparability_decision_is_persisted_with_its_reason_code():
    """ADR-004: comparing two runs *always* produces a persisted decision with a
    reason code, whether the answer is comparable, not comparable, or that a run
    does not exist. Nothing is decided silently."""

    sdk = WorldSDK(db_url="sqlite://")
    _evaluate(sdk, "eval:p-1", "truth-v1")
    _evaluate(sdk, "eval:p-2", "truth-v1")
    _evaluate(sdk, "eval:p-3", "truth-v2")

    comparable = sdk.compare_runs("eval:p-1", "eval:p-2")
    mismatched = sdk.compare_runs("eval:p-1", "eval:p-3")
    missing = sdk.compare_runs("eval:p-1", "eval:does-not-exist")

    assert (comparable.decision, comparable.reason_code) == ("comparable", "COMPARABLE")
    assert (mismatched.decision, mismatched.reason_code) == ("not_comparable", "TEST_SET_VERSION_MISMATCH")
    assert (missing.decision, missing.reason_code) == ("not_comparable", "RUN_NOT_FOUND")

    with Session(sdk.runtime.engine) as session:
        records = session.exec(select(ComparabilityDecisionRecord).order_by(ComparabilityDecisionRecord.id.asc())).all()
        events = session.exec(
            select(WorldEvent).where(WorldEvent.event_type == "comparability_decided").order_by(WorldEvent.id.asc())
        ).all()

    assert [(r.run_a_id, r.run_b_id, r.decision, r.reason_code) for r in records] == [
        ("eval:p-1", "eval:p-2", "comparable", "COMPARABLE"),
        ("eval:p-1", "eval:p-3", "not_comparable", "TEST_SET_VERSION_MISMATCH"),
        ("eval:p-1", "eval:does-not-exist", "not_comparable", "RUN_NOT_FOUND"),
    ]
    assert records[1].details["test_set_version_b"] == "truth-v2"

    # The decision is also an event in the causal log, keyed by the pair it decided.
    assert [e.stable_id for e in events] == [
        "eval:p-1::eval:p-2",
        "eval:p-1::eval:p-3",
        "eval:p-1::eval:does-not-exist",
    ]
    assert [e.payload["reason_code"] for e in events] == ["COMPARABLE", "TEST_SET_VERSION_MISMATCH", "RUN_NOT_FOUND"]
