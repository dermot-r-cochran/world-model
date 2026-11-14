"""The runtime's refusals, one rule to a test, each checked twice over: the
command raises the error that names the rule, and the store holds exactly what
it held before. A refusal that half-writes is not a refusal.

The refusals proved elsewhere are not repeated here: the identity prefix, a
transition the rules do not allow and a claim without evidence
(test_spec_runtime_rules.py), and re-creating an identity that exists
(tests/regression/test_recreate_cannot_bypass_transitions.py)."""

import pytest
from sqlmodel import Session, select

from worldruntime import (
    EntityVersion,
    EvaluationRunRecord,
    EvidenceError,
    EvidenceRecord,
    IdentityError,
    InvariantError,
    RelationRecord,
    TransitionError,
    WorldEvent,
)
from worldsdk import WorldSDK
from worldspec import default_document_world_spec

TABLES = (EntityVersion, RelationRecord, EvidenceRecord, WorldEvent, EvaluationRunRecord)


def _stored(sdk: WorldSDK) -> dict[str, int]:
    # Rows per table: what a refused command must leave as it found it.
    with Session(sdk.runtime.engine) as session:
        return {table.__name__: len(session.exec(select(table)).all()) for table in TABLES}


def test_an_entity_type_outside_the_ontology_is_refused():
    sdk = WorldSDK(db_url="sqlite://")
    before = _stored(sdk)

    with pytest.raises(IdentityError, match="Unknown entity type"):
        sdk.create_entity("inv:500", "invoice")

    assert _stored(sdk) == before
    assert sdk.world_view("inv:500") == {}


def test_an_entity_cannot_be_created_in_a_state_outside_its_lifecycle():
    sdk = WorldSDK(db_url="sqlite://")
    before = _stored(sdk)

    # A document is draft, ingested or processed; "archived" is none of them.
    with pytest.raises(TransitionError, match="Invalid state 'archived'"):
        sdk.create_entity("doc:510", "document", state="archived")

    assert _stored(sdk) == before
    assert sdk.world_view("doc:510") == {}


def test_an_evidence_id_is_used_once():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("row:520", "extracted_row", state="active")
    sdk.create_entity("row:521", "extracted_row", state="active")
    sdk.attach_evidence("ev:520", "row:520", source_ref="inv-520.pdf#p1", excerpt="Total: 52.00")
    before = _stored(sdk)

    with pytest.raises(EvidenceError, match="Duplicate evidence_id"):
        sdk.attach_evidence("ev:520", "row:521", source_ref="inv-521.pdf#p1", excerpt="Total: 99.00")

    assert _stored(sdk) == before
    # The id still means what it meant: the first row's evidence, unaltered.
    assert [(e["evidence_id"], e["excerpt"]) for e in sdk.world_view("row:520")["evidence"]] == [("ev:520", "Total: 52.00")]
    assert sdk.world_view("row:521")["evidence"] == []


def test_a_relation_needs_both_of_its_endpoints():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("doc:530", "document")
    sdk.create_entity("sec:530:totals", "section", state="active")
    before = _stored(sdk)

    with pytest.raises(IdentityError, match="endpoints must exist"):
        sdk.create_relation("contains", "doc:530", "sec:530:never")
    with pytest.raises(IdentityError, match="endpoints must exist"):
        sdk.create_relation("contains", "doc:never", "sec:530:totals")

    assert _stored(sdk) == before
    assert sdk.world_view("doc:530")["relations"] == []
    assert sdk.world_view("sec:530:totals")["relations"] == []


def test_a_relation_the_ontology_does_not_declare_is_refused():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("doc:540", "document")
    sdk.create_entity("sec:540:totals", "section", state="active")
    before = _stored(sdk)

    # The ontology declares contains as document -> section. The same name the
    # other way round is not that relation, and "cites" is declared nowhere.
    with pytest.raises(IdentityError, match="not allowed for section->document"):
        sdk.create_relation("contains", "sec:540:totals", "doc:540")
    with pytest.raises(IdentityError, match="cites not allowed"):
        sdk.create_relation("cites", "doc:540", "sec:540:totals")

    assert _stored(sdk) == before

    # The declared relation, between the same two entities, is accepted.
    sdk.create_relation("contains", "doc:540", "sec:540:totals")
    assert [(r["relation_type"], r["source_stable_id"], r["target_stable_id"]) for r in sdk.world_view("doc:540")["relations"]] == [
        ("contains", "doc:540", "sec:540:totals")
    ]


def test_an_unknown_identity_cannot_be_transitioned():
    sdk = WorldSDK(db_url="sqlite://")
    before = _stored(sdk)

    with pytest.raises(TransitionError, match="unknown entity"):
        sdk.transition("doc:550", "ingested", reason="parse complete")

    # Refusing the transition did not bring the entity into being.
    assert _stored(sdk) == before
    assert sdk.world_view("doc:550") == {}


def test_a_spec_can_require_evidence_for_every_transition():
    # The default spec leaves evidence optional on a transition; this one
    # switches the rule on, which no other test does.
    spec = default_document_world_spec()
    spec.evidence_rule.require_evidence_for_transitions = True
    sdk = WorldSDK(db_url="sqlite://", spec=spec)
    sdk.create_entity("doc:560", "document")
    sdk.attach_evidence("ev:560", "doc:560", source_ref="inv-560.pdf", excerpt="Parsed 3 pages")
    before = _stored(sdk)

    with pytest.raises(EvidenceError, match="Transition requires evidence"):
        sdk.transition("doc:560", "ingested", reason="parse complete")

    assert _stored(sdk) == before
    world_view = sdk.world_view("doc:560")
    assert (world_view["state"], world_view["version"]) == ("draft", 1)

    # With its evidence the same transition goes through, and the event says
    # which evidence it stood on.
    moved = sdk.transition("doc:560", "ingested", reason="parse complete", evidence_id="ev:560")
    assert (moved.state, moved.version) == ("ingested", 2)
    transitions = [e for e in sdk.world_view("doc:560")["events"] if e["event_type"] == "state_transition"]
    assert [e["evidence_id"] for e in transitions] == ["ev:560"]


def test_a_transition_cannot_cite_evidence_that_does_not_exist():
    # Under the default spec a transition needs no evidence, but one that
    # names evidence must name evidence that is there.
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("doc:570", "document")
    before = _stored(sdk)

    with pytest.raises(EvidenceError, match="Transition evidence not found"):
        sdk.transition("doc:570", "ingested", reason="parse complete", evidence_id="ev:never")

    assert _stored(sdk) == before
    world_view = sdk.world_view("doc:570")
    assert (world_view["state"], world_view["version"]) == ("draft", 1)


def test_a_claim_needs_a_subject_that_exists():
    sdk = WorldSDK(db_url="sqlite://")
    # The evidence is real, so the missing subject is the only thing wrong.
    sdk.create_entity("row:580", "extracted_row", state="active")
    sdk.attach_evidence("ev:580", "row:580", source_ref="inv-580.pdf#p1", excerpt="Total: 58.00")
    before = _stored(sdk)

    with pytest.raises(EvidenceError, match="Claim subject must exist"):
        sdk.create_claim(
            claim_id="claim:581",
            stable_id="row:581",
            claim_type="field_extracted",
            payload={"field": "total", "value": "58.00"},
            evidence_id="ev:580",
        )

    assert _stored(sdk) == before
    assert sdk.world_view("row:581") == {}


def test_a_claim_cannot_cite_evidence_that_does_not_exist():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("row:590", "extracted_row", state="active")
    before = _stored(sdk)

    with pytest.raises(EvidenceError, match="Claim evidence not found"):
        sdk.create_claim(
            claim_id="claim:590",
            stable_id="row:590",
            claim_type="field_extracted",
            payload={"field": "total", "value": "59.00"},
            evidence_id="ev:never",
        )

    assert _stored(sdk) == before
    assert [e["event_type"] for e in sdk.world_view("row:590")["events"]] == ["entity_created"]


def test_a_run_id_is_recorded_once():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.evaluate_run(
        run_id="eval:600",
        test_set_version="truth-v1",
        alignment_strategy="stable_id",
        extracted_rows=[{"row_id": "row:1", "value": "10"}],
        truth_rows=[{"row_id": "row:1", "value": "10"}],
    )
    before = _stored(sdk)

    with pytest.raises(InvariantError, match="run_id already exists"):
        sdk.evaluate_run(
            run_id="eval:600",
            test_set_version="truth-v2",
            alignment_strategy="stable_id",
            extracted_rows=[{"row_id": "row:1", "value": "12"}],
            truth_rows=[{"row_id": "row:1", "value": "10"}],
        )

    assert _stored(sdk) == before
    # The run on record is still the first one, not the one that was refused.
    recorded = sdk.runtime.get_evaluation_run("eval:600")
    assert (recorded.test_set_version, recorded.metrics["precision"]) == ("truth-v1", 1.0)
