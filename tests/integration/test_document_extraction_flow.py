from worldsdk import WorldSDK


def test_end_to_end_document_extraction_flow():
    sdk = WorldSDK(db_url="sqlite://")

    sdk.create_entity("doc:inv-1", "document")
    sdk.create_entity("sec:inv-1:totals", "section", state="active")
    sdk.create_relation("contains", "doc:inv-1", "sec:inv-1:totals")

    sdk.create_entity("row:inv-1:total", "extracted_row", state="active", attributes={"value": "500"})
    sdk.create_relation("supports", "sec:inv-1:totals", "row:inv-1:total")

    sdk.attach_evidence(
        evidence_id="ev-1",
        subject_stable_id="row:inv-1:total",
        source_ref="inv-1.pdf#p1:120-160",
        excerpt="Total: 500",
    )

    sdk.create_claim(
        claim_id="claim-1",
        stable_id="row:inv-1:total",
        claim_type="field_extracted",
        payload={"field": "total", "value": "500"},
        evidence_id="ev-1",
    )

    sdk.transition("doc:inv-1", "ingested", reason="ingestion complete")

    run = sdk.evaluate_run(
        run_id="eval:doc-1",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:inv-1:total", "value": "500"}],
        truth_rows=[{"row_id": "row:inv-1:total", "value": "500"}],
    )

    world_view = sdk.world_view("row:inv-1:total")

    assert run.metrics["precision"] == 1.0
    assert len(run.mismatches) == 0
    assert len(world_view["evidence"]) == 1
    assert any(event["event_type"] == "claim_created" for event in world_view["events"])
