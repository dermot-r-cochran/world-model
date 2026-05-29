from worldsdk import WorldSDK


def test_invariant_requires_evidence_for_extracted_row():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("row:200", "extracted_row", state="active", attributes={"field": "invoice_total"})

    violations = sdk.enforce_invariants(["row:200"])

    assert len(violations) == 1
    assert violations[0].code == "ROW_EVIDENCE_REQUIRED"
