"""Run a small end-to-end demo of the world view SDK."""

from worldview.domain import ClaimCreate, EntityCreate, EvidenceCreate, TransitionCommand
from worldview.sdk import WorldViewSDK


def main() -> None:
    sdk = WorldViewSDK(db_url="sqlite:///./demo_worldview.db")

    sdk.create_entity(
        EntityCreate(
            stable_id="doc:invoice-001",
            entity_type="document",
            state="draft",
            attributes={"title": "Invoice 001"},
        )
    )
    sdk.create_entity(
        EntityCreate(
            stable_id="sec:invoice-001:totals",
            entity_type="section",
            state="parsed",
            attributes={"heading": "Totals"},
        )
    )

    evidence = sdk.add_evidence(
        EvidenceCreate(
            evidence_id="ev-001",
            subject_stable_id="doc:invoice-001",
            source_ref="invoice-001.pdf#p1:120-180",
            excerpt="Total due: 500 USD",
        )
    )

    sdk.apply_transition(
        TransitionCommand(
            stable_id="doc:invoice-001",
            to_state="ingested",
            reason="Document parsed",
            evidence_id=evidence.evidence_id,
        )
    )

    sdk.create_claim(
        ClaimCreate(
            claim_id="claim-001",
            stable_id="doc:invoice-001",
            claim_type="document_total_extracted",
            payload={"total": 500, "currency": "USD"},
            evidence_id=evidence.evidence_id,
        )
    )

    print(sdk.world_view("doc:invoice-001"))


if __name__ == "__main__":
    main()
