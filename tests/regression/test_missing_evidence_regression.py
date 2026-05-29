from fastapi.testclient import TestClient

from worldview.api import create_app


def test_regression_claim_without_evidence_is_rejected():
    app = create_app(db_url="sqlite://")
    client = TestClient(app)

    client.post(
        "/entities",
        json={
            "stable_id": "doc:reg-1",
            "entity_type": "document",
            "state": "draft",
            "attributes": {},
        },
    )

    response = client.post(
        "/claims",
        json={
            "claim_id": "claim-reg-1",
            "stable_id": "doc:reg-1",
            "claim_type": "total_extracted",
            "payload": {"total": 42},
        },
    )
    assert response.status_code == 400
    assert "Claims must reference evidence_id" in response.json()["detail"]
