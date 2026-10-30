"""The README's quick start ends with `uvicorn worldsdk.api:create_app --factory`.
These tests drive that app through Starlette's TestClient (httpx, already in
the dev extra) on a file, the way the quick start runs it: every route once,
the SDK's refusals arriving as HTTP errors, and what the app wrote read back
by a second app on the same file."""

from fastapi.testclient import TestClient

from worldsdk import create_app


def _db_url(tmp_path) -> str:
    return f"sqlite:///{(tmp_path / 'api.db').as_posix()}"


def test_api_round_trip_over_the_sdk(tmp_path):
    db_url = _db_url(tmp_path)

    with TestClient(create_app(db_url=db_url)) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok", "worldview_profile": "enterprise-doc-default"}

        created = client.post(
            "/entities",
            json={"stable_id": "doc:api-1", "entity_type": "document", "attributes": {"title": "Invoice"}},
        )
        assert created.status_code == 200
        assert (created.json()["state"], created.json()["version"]) == ("draft", 1)

        row = client.post("/entities", json={"stable_id": "row:api-1:total", "entity_type": "extracted_row", "state": "active"})
        assert row.status_code == 200

        evidence = client.post(
            "/evidence",
            json={
                "evidence_id": "ev:api-1",
                "subject_stable_id": "row:api-1:total",
                "source_ref": "invoice.pdf#p1",
                "excerpt": "Total: 500",
            },
        )
        assert evidence.status_code == 200
        assert evidence.json()["evidence_id"] == "ev:api-1"
        assert evidence.json()["source_system"] == "system_of_record"

        moved = client.post("/transitions", json={"stable_id": "doc:api-1", "to_state": "ingested", "reason": "parse complete"})
        assert moved.status_code == 200
        assert (moved.json()["state"], moved.json()["version"]) == ("ingested", 2)

        for run_id in ("eval:api-a", "eval:api-b"):
            run = client.post(
                "/evaluate",
                json={
                    "run_id": run_id,
                    "test_set_version": "truth-v1",
                    "alignment_strategy": "stable_id",
                    "extracted_rows": [{"row_id": "row:api-1:total", "value": "500"}],
                    "truth_rows": [{"row_id": "row:api-1:total", "value": "500"}],
                },
            )
            assert run.status_code == 200
            assert run.json()["metrics"]["precision"] == 1.0
            assert run.json()["mismatches"] == []

        decision = client.post("/compare-runs", json={"run_a_id": "eval:api-a", "run_b_id": "eval:api-b"})
        assert decision.status_code == 200
        assert (decision.json()["decision"], decision.json()["reason_code"]) == ("comparable", "COMPARABLE")

        document = client.get("/world-view/doc:api-1")
        assert document.status_code == 200
        assert (document.json()["state"], document.json()["version"]) == ("ingested", 2)
        assert document.json()["attributes"] == {"title": "Invoice"}
        assert [e["event_type"] for e in document.json()["events"]] == ["entity_created", "state_transition"]

        row_view = client.get("/world-view/row:api-1:total").json()
        assert [e["evidence_id"] for e in row_view["evidence"]] == ["ev:api-1"]

    # The app wrote to the file, not to the process: a fresh app on the same
    # file serves the same world.
    with TestClient(create_app(db_url=db_url)) as again:
        reopened = again.get("/world-view/doc:api-1")
        assert reopened.status_code == 200
        assert (reopened.json()["state"], reopened.json()["version"]) == ("ingested", 2)


def test_api_turns_refusals_into_http_errors_not_silent_writes(tmp_path):
    with TestClient(create_app(db_url=_db_url(tmp_path))) as client:
        # Identity rule (ADR-002): a stable_id without its prefix is refused
        # with the rule's own message, and nothing is written.
        bad_id = client.post("/entities", json={"stable_id": "bad-doc-id", "entity_type": "document"})
        assert bad_id.status_code == 400
        assert "doc:" in bad_id.json()["detail"]
        assert client.get("/world-view/bad-doc-id").status_code == 404

        # A request missing a required field never reaches the SDK.
        assert client.post("/entities", json={"entity_type": "document"}).status_code == 422

        # Transition rules: ingested -> draft is refused and the entity stays put.
        client.post("/entities", json={"stable_id": "doc:api-2", "entity_type": "document"})
        client.post("/transitions", json={"stable_id": "doc:api-2", "to_state": "ingested", "reason": "parse complete"})
        refused = client.post("/transitions", json={"stable_id": "doc:api-2", "to_state": "draft", "reason": "back"})
        assert refused.status_code == 400
        assert "not allowed" in refused.json()["detail"]
        after = client.get("/world-view/doc:api-2").json()
        assert (after["state"], after["version"]) == ("ingested", 2)

        # Evidence needs a subject that exists.
        orphan = client.post(
            "/evidence",
            json={"evidence_id": "ev:orphan", "subject_stable_id": "row:nobody", "source_ref": "x", "excerpt": "y"},
        )
        assert orphan.status_code == 400
        assert "must exist" in orphan.json()["detail"]

        # An unknown identity is a 404, not an empty world.
        assert client.get("/world-view/doc:never").status_code == 404
