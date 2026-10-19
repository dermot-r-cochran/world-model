import pytest
from sqlmodel import Session, select

from worldruntime import ComparabilityDecisionRecord, TransitionError
from worldsdk import WorldSDK


def test_state_evidence_events_and_runs_survive_a_restart(tmp_path):
    """The README's first word is "durable": what one WorldSDK wrote, a fresh
    WorldSDK opened on the same file must read back unchanged."""

    db_url = f"sqlite:///{(tmp_path / 'world.db').as_posix()}"

    first = WorldSDK(db_url=db_url)
    first.create_entity("doc:restart-1", "document", attributes={"title": "Invoice"})
    first.create_entity("row:restart-1:total", "extracted_row", state="active")
    first.attach_evidence(
        evidence_id="ev:restart-1",
        subject_stable_id="row:restart-1:total",
        source_ref="invoice.pdf#p1",
        excerpt="Total: 500",
    )
    first.transition("doc:restart-1", "ingested", reason="parse complete")
    first.evaluate_run(
        run_id="eval:restart-a",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:restart-1:total", "value": "500"}],
        truth_rows=[{"row_id": "row:restart-1:total", "value": "500"}],
    )
    first.evaluate_run(
        run_id="eval:restart-b",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:restart-1:total", "value": "500"}],
        truth_rows=[{"row_id": "row:restart-1:total", "value": "500"}],
    )
    first.compare_runs("eval:restart-a", "eval:restart-b")
    first.runtime.engine.dispose()
    del first

    second = WorldSDK(db_url=db_url)

    document = second.world_view("doc:restart-1")
    assert document["state"] == "ingested"
    assert document["version"] == 2
    assert document["attributes"] == {"title": "Invoice"}
    assert [e["event_type"] for e in document["events"]] == ["entity_created", "state_transition"]

    row = second.world_view("row:restart-1:total")
    assert [e["evidence_id"] for e in row["evidence"]] == ["ev:restart-1"]

    run = second.runtime.get_evaluation_run("eval:restart-a")
    assert run is not None
    assert run.metrics["precision"] == 1.0

    with Session(second.runtime.engine) as session:
        decisions = session.exec(
            select(ComparabilityDecisionRecord).where(ComparabilityDecisionRecord.run_a_id == "eval:restart-a")
        ).all()
    assert [d.reason_code for d in decisions] == ["COMPARABLE"]

    # The rules still bind over the reopened state: ingested -> draft stays refused.
    with pytest.raises(TransitionError):
        second.transition("doc:restart-1", "draft", reason="invalid back transition")
    assert second.world_view("doc:restart-1")["version"] == 2

    second.runtime.engine.dispose()
