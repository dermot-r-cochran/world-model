"""Until 2026-11-11 enforce_invariants() with no ids checked every stored
version of an entity, while enforce_invariants([id]) checked the latest only,
so an entity with two versions and no evidence got two violations from the
first call and one from the second. Both now judge the latest version."""

from worldspec import StateModel, TransitionRule, default_document_world_spec
from worldsdk import WorldSDK


def _sdk_whose_rows_can_transition() -> WorldSDK:
    # The default spec gives extracted_row no transitions, so no row can have a
    # second version; this one lets a row be reviewed.
    spec = default_document_world_spec()
    spec.state_models.append(
        StateModel(entity_type="extracted_row", initial_state="extracted", allowed_states={"extracted", "reviewed"})
    )
    spec.transition_rules.append(TransitionRule(entity_type="extracted_row", from_state="extracted", to_state="reviewed"))
    return WorldSDK(db_url="sqlite://", spec=spec)


def test_regression_invariants_judge_the_latest_version_with_or_without_ids():
    sdk = _sdk_whose_rows_can_transition()
    sdk.create_entity("row:400", "extracted_row")
    sdk.transition("row:400", "reviewed", reason="checked by hand")
    assert sdk.world_view("row:400")["version"] == 2

    with_ids = sdk.enforce_invariants(["row:400"])
    without_ids = sdk.enforce_invariants()

    assert [(v.code, v.stable_id) for v in with_ids] == [("ROW_EVIDENCE_REQUIRED", "row:400")]
    assert [(v.code, v.stable_id) for v in without_ids] == [("ROW_EVIDENCE_REQUIRED", "row:400")]

    # Once the row has its evidence, neither call reports it.
    sdk.attach_evidence("ev:400", "row:400", source_ref="inv-400.pdf#p1", excerpt="Total: 40.00")
    assert sdk.enforce_invariants(["row:400"]) == []
    assert sdk.enforce_invariants() == []
