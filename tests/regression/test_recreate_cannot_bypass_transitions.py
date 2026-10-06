import pytest

from worldruntime import IdentityError, TransitionError
from worldsdk import WorldSDK


def test_regression_recreating_an_entity_cannot_perform_a_refused_transition():
    sdk = WorldSDK(db_url="sqlite://")
    sdk.create_entity("doc:300", "document")
    sdk.transition("doc:300", "ingested", reason="parse complete")

    # The rules refuse ingested -> draft ...
    with pytest.raises(TransitionError):
        sdk.transition("doc:300", "draft", reason="invalid back transition")

    # ... and re-creating the same stable_id in that state must not do it either.
    with pytest.raises(IdentityError):
        sdk.create_entity("doc:300", "document", state="draft")

    world_view = sdk.world_view("doc:300")
    assert world_view["state"] == "ingested"
    assert world_view["version"] == 2
    assert [e["event_type"] for e in world_view["events"]] == ["entity_created", "state_transition"]
