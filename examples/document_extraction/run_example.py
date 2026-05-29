"""Example application demonstrating document extraction and governed evaluation flow."""

from worldsdk import WorldSDK


def main() -> None:
    sdk = WorldSDK(db_url="sqlite:///./document_example.db")

    sdk.create_entity("doc:inv-100", "document", attributes={"title": "Invoice INV-100"})
    sdk.create_entity("sec:inv-100:totals", "section", state="active", attributes={"heading": "Totals"})
    sdk.create_relation("contains", "doc:inv-100", "sec:inv-100:totals")

    sdk.create_entity("row:inv-100:total", "extracted_row", state="active", attributes={"field": "total", "value": "500"})
    sdk.create_relation("supports", "sec:inv-100:totals", "row:inv-100:total")

    sdk.attach_evidence(
        evidence_id="ev-100",
        subject_stable_id="row:inv-100:total",
        source_ref="inv-100.pdf#p1:120-170",
        excerpt="Total due: 500 USD",
    )

    sdk.create_claim(
        claim_id="claim-100",
        stable_id="row:inv-100:total",
        claim_type="field_extracted",
        payload={"field": "total", "value": "500"},
        evidence_id="ev-100",
    )

    sdk.transition("doc:inv-100", "ingested", reason="Document parsed")

    violations = sdk.enforce_invariants(["row:inv-100:total"])
    print(f"Invariant violations: {len(violations)}")

    run_1 = sdk.evaluate_run(
        run_id="eval:run-1",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:inv-100:total", "value": "500"}],
        truth_rows=[{"row_id": "row:inv-100:total", "value": "500"}],
    )

    run_2 = sdk.evaluate_run(
        run_id="eval:run-2",
        test_set_version="truth-v1",
        alignment_strategy="value_fallback",
        extracted_rows=[{"row_id": "row:inv-100:total", "value": "520"}],
        truth_rows=[{"row_id": "row:inv-100:total", "value": "500"}],
    )

    decision = sdk.compare_runs("eval:run-1", "eval:run-2")

    print("Run 1 metrics:", run_1.metrics)
    print("Run 2 metrics:", run_2.metrics)
    print("Comparability decision:", decision.model_dump())
    print("World view snapshot:", sdk.world_view("row:inv-100:total"))


if __name__ == "__main__":
    main()
