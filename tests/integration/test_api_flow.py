from fastapi.testclient import TestClient

from worldview.api import create_app


def test_api_end_to_end_flow():
    app = create_app(db_url="sqlite://")
    client = TestClient(app)

    create_doc = client.post(
        "/entities",
        json={
            "stable_id": "doc:int-1",
            "entity_type": "document",
            "state": "draft",
            "attributes": {"name": "Invoice"},
        },
    )
    assert create_doc.status_code == 200

    evidence = client.post(
        "/evidence",
        json={
            "evidence_id": "ev-int-1",
            "subject_stable_id": "doc:int-1",
            "source_ref": "invoice.pdf#p1",
            "excerpt": "Total: 10",
            "metadata": {},
        },
    )
    assert evidence.status_code == 200

    transition = client.post(
        "/transitions",
        json={
            "stable_id": "doc:int-1",
            "to_state": "ingested",
            "reason": "ingestion complete",
            "evidence_id": "ev-int-1",
        },
    )
    assert transition.status_code == 200

    claim = client.post(
        "/claims",
        json={
            "claim_id": "claim-int-1",
            "stable_id": "doc:int-1",
            "claim_type": "total_extracted",
            "payload": {"total": 10},
            "evidence_id": "ev-int-1",
        },
    )
    assert claim.status_code == 200

    view = client.get("/world-view/doc:int-1")
    assert view.status_code == 200
    body = view.json()
    assert body["stable_id"] == "doc:int-1"
    assert body["state"] == "ingested"
    assert len(body["evidence"]) == 1
    assert any(event["event_type"] == "claim_created" for event in body["events"])
