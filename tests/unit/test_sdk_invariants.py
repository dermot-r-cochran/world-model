from worldview.domain import ClaimCreate, EntityCreate, EvidenceCreate, TransitionCommand
from worldview.errors import EvidenceViolation, TransitionViolation
from worldview.sdk import WorldViewSDK


def test_stable_identity_versions_increment():
    sdk = WorldViewSDK(db_url="sqlite://")
    one = sdk.create_entity(EntityCreate(stable_id="doc:1", entity_type="document", state="draft"))
    two = sdk.create_entity(EntityCreate(stable_id="doc:1", entity_type="document", state="draft"))
    assert one.version == 1
    assert two.version == 2


def test_transition_rule_enforced():
    sdk = WorldViewSDK(db_url="sqlite://")
    sdk.create_entity(EntityCreate(stable_id="doc:2", entity_type="document", state="draft"))

    try:
        sdk.apply_transition(
            TransitionCommand(stable_id="doc:2", to_state="processed", reason="skip invalid")
        )
        raised = False
    except TransitionViolation:
        raised = True

    assert raised


def test_claim_requires_evidence():
    sdk = WorldViewSDK(db_url="sqlite://")
    sdk.create_entity(EntityCreate(stable_id="doc:3", entity_type="document", state="draft"))

    try:
        sdk.create_claim(
            ClaimCreate(
                claim_id="c1",
                stable_id="doc:3",
                claim_type="assertion",
                payload={"ok": True},
                evidence_id=None,
            )
        )
        raised = False
    except EvidenceViolation:
        raised = True

    assert raised


def test_claim_with_evidence_succeeds():
    sdk = WorldViewSDK(db_url="sqlite://")
    sdk.create_entity(EntityCreate(stable_id="doc:4", entity_type="document", state="draft"))
    ev = sdk.add_evidence(
        EvidenceCreate(
            evidence_id="ev-4",
            subject_stable_id="doc:4",
            source_ref="file#1",
            excerpt="proof",
        )
    )
    claim = sdk.create_claim(
        ClaimCreate(
            claim_id="c2",
            stable_id="doc:4",
            claim_type="assertion",
            payload={"ok": True},
            evidence_id=ev.evidence_id,
        )
    )
    assert claim.event_type == "claim_created"
