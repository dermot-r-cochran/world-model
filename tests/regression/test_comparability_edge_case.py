from worldsdk import WorldSDK


def test_regression_runs_with_different_test_set_versions_not_comparable():
    sdk = WorldSDK(db_url="sqlite://")

    sdk.evaluate_run(
        run_id="eval:reg-a",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:1", "value": "10"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )
    sdk.evaluate_run(
        run_id="eval:reg-b",
        test_set_version="truth-v2",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:1", "value": "10"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )

    decision = sdk.compare_runs("eval:reg-a", "eval:reg-b")

    assert decision.decision == "not_comparable"
    assert decision.reason_code == "TEST_SET_VERSION_MISMATCH"
