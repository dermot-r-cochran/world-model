from worldruntime import EvidenceError, IdentityError, TransitionError
from worldsdk import WorldSDK


def test_identity_rules_enforced_by_prefix():
    sdk = WorldSDK(db_url="sqlite://")

    try:
        sdk.create_entity("bad-doc-id", "document")
        raised = False
    except IdentityError:
        raised = True

    assert raised


def test_valid_and_invalid_transitions():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("doc:100", "document")
    sdk.transition("doc:100", "ingested", reason="parse complete")

    try:
        sdk.transition("doc:100", "draft", reason="invalid back transition")
        raised = False
    except TransitionError:
        raised = True

    assert raised


def test_claim_requires_evidence():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("row:100", "extracted_row", state="active")

    try:
        sdk.create_claim(
            claim_id="claim:100",
            stable_id="row:100",
            claim_type="field_extracted",
            payload={"field": "total", "value": "100"},
            evidence_id=None,
        )
        raised = False
    except EvidenceError:
        raised = True

    assert raised
