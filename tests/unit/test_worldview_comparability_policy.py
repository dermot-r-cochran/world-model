from worldsdk import WorldSDK


def test_comparability_decision_rejects_alignment_mismatch():
    sdk = WorldSDK(db_url="sqlite://")

    sdk.evaluate_run(
        run_id="eval:1",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:1", "value": "10"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )
    sdk.evaluate_run(
        run_id="eval:2",
        test_set_version="truth-v1",
        alignment_strategy="value_fallback",
        extracted_rows=[{"row_id": "row:1", "value": "12"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )

    decision = sdk.compare_runs("eval:1", "eval:2")

    assert decision.decision == "not_comparable"
    assert decision.reason_code == "ALIGNMENT_STRATEGY_MISMATCH"
