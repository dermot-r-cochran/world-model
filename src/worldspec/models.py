"""Typed ASM contracts defining semantic and normative world structure."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EntityType(BaseModel):
    """Domain entity type with stable identity and lifecycle semantics."""

    name: str
    description: str


class RelationType(BaseModel):
    """Typed relation constraints between source and target entity types."""

    name: str
    source_type: str
    target_type: str


class IdentityRule(BaseModel):
    """Identity policy for one entity type."""

    entity_type: str
    required_prefix: str


class StateModel(BaseModel):
    """Allowed states and default initial state for one entity type."""

    entity_type: str
    initial_state: str
    allowed_states: set[str]


class TransitionRule(BaseModel):
    """Allowed directed transition between two states for an entity type."""

    entity_type: str
    from_state: str
    to_state: str


class EvidenceRule(BaseModel):
    """Evidence requirements for claims and transition events."""

    require_evidence_for_claims: bool = True
    require_evidence_for_transitions: bool = False
    required_evidence_for_entity_types: set[str] = Field(default_factory=set)


class InvariantSpec(BaseModel):
    """Declarative invariant specification used by runtime enforcement."""

    code: str
    description: str
    severity: str = "error"


class ComparabilityPolicy(BaseModel):
    """Policy controlling when two evaluation runs are comparable."""

    require_same_worldview_profile: bool = True
    require_same_test_set_version: bool = True
    require_same_alignment_strategy: bool = True
    allow_fallback_alignment_when_identity_missing: bool = False


class AccountabilityMapping(BaseModel):
    """Ownership mapping for mismatch or violation classes."""

    owner_by_class: dict[str, str] = Field(default_factory=dict)


class WorldViewProfile(BaseModel):
    """Typed worldview policy artifact for interpretation and governance."""

    name: str
    trust_hierarchy: list[str]
    ambiguity_policy: str
    fallback_alignment_strategy: str
    comparability_policy: ComparabilityPolicy
    escalation_policy: dict[str, str] = Field(default_factory=dict)
    accountability: AccountabilityMapping = Field(default_factory=AccountabilityMapping)


class WorldSpec(BaseModel):
    """Complete ASM specification: ontology, identity, evidence, transitions, invariants."""

    entity_types: list[EntityType]
    relation_types: list[RelationType]
    identity_rules: list[IdentityRule]
    state_models: list[StateModel]
    transition_rules: list[TransitionRule]
    evidence_rule: EvidenceRule
    invariants: list[InvariantSpec]

    @model_validator(mode="after")
    def validate_transition_rules_against_state_models(self) -> "WorldSpec":
        """Ensure transition rules only reference known states for each entity lifecycle."""

        state_models = {model.entity_type: model for model in self.state_models}
        for rule in self.transition_rules:
            state_model = state_models.get(rule.entity_type)
            if state_model is None:
                continue
            if rule.from_state not in state_model.allowed_states or rule.to_state not in state_model.allowed_states:
                raise ValueError(
                    f"Transition rule {rule.entity_type}:{rule.from_state}->{rule.to_state} "
                    "references states outside allowed_states"
                )
        return self

    def has_entity_type(self, entity_type: str) -> bool:
        return any(e.name == entity_type for e in self.entity_types)

    def relation_allowed(self, relation_name: str, source_type: str, target_type: str) -> bool:
        return any(
            rel.name == relation_name and rel.source_type == source_type and rel.target_type == target_type
            for rel in self.relation_types
        )

    def identity_rule_for(self, entity_type: str) -> IdentityRule | None:
        return next((rule for rule in self.identity_rules if rule.entity_type == entity_type), None)

    def state_model_for(self, entity_type: str) -> StateModel | None:
        return next((model for model in self.state_models if model.entity_type == entity_type), None)

    def transition_allowed(self, entity_type: str, from_state: str, to_state: str) -> bool:
        return any(
            rule.entity_type == entity_type and rule.from_state == from_state and rule.to_state == to_state
            for rule in self.transition_rules
        )


def default_document_world_spec() -> WorldSpec:
    """Default business-ready spec for document extraction and evaluation workflows."""

    return WorldSpec(
        entity_types=[
            EntityType(name="document", description="Source business document"),
            EntityType(name="section", description="Document section or chunk"),
            EntityType(name="extracted_row", description="Structured extraction row"),
            EntityType(name="truth_row", description="Reference truth row"),
            EntityType(name="evaluation_run", description="Evaluation execution metadata"),
            EntityType(name="error_class", description="Mismatch taxonomy class"),
            EntityType(name="owner_team", description="Accountability owner for mismatch class"),
        ],
        relation_types=[
            RelationType(name="contains", source_type="document", target_type="section"),
            RelationType(name="supports", source_type="section", target_type="extracted_row"),
            RelationType(name="classified_as", source_type="extracted_row", target_type="error_class"),
            RelationType(name="owned_by", source_type="error_class", target_type="owner_team"),
        ],
        identity_rules=[
            IdentityRule(entity_type="document", required_prefix="doc:"),
            IdentityRule(entity_type="section", required_prefix="sec:"),
            IdentityRule(entity_type="extracted_row", required_prefix="row:"),
            IdentityRule(entity_type="truth_row", required_prefix="truth:"),
            IdentityRule(entity_type="evaluation_run", required_prefix="eval:"),
            IdentityRule(entity_type="error_class", required_prefix="err:"),
            IdentityRule(entity_type="owner_team", required_prefix="team:"),
        ],
        state_models=[
            StateModel(entity_type="document", initial_state="draft", allowed_states={"draft", "ingested", "processed"}),
            StateModel(entity_type="evaluation_run", initial_state="created", allowed_states={"created", "running", "completed"}),
        ],
        transition_rules=[
            TransitionRule(entity_type="document", from_state="draft", to_state="ingested"),
            TransitionRule(entity_type="document", from_state="ingested", to_state="processed"),
            TransitionRule(entity_type="evaluation_run", from_state="created", to_state="running"),
            TransitionRule(entity_type="evaluation_run", from_state="running", to_state="completed"),
        ],
        evidence_rule=EvidenceRule(
            require_evidence_for_claims=True,
            require_evidence_for_transitions=False,
            required_evidence_for_entity_types={"extracted_row"},
        ),
        invariants=[
            InvariantSpec(code="ROW_EVIDENCE_REQUIRED", description="Every extracted row must have evidence"),
            InvariantSpec(code="UNKNOWN_ERROR_CLASS_SURFACED", description="Unknown mismatch classes are violations"),
        ],
    )


def default_document_worldview_profile() -> WorldViewProfile:
    """Default worldview policy for document extraction reliability workflows."""

    return WorldViewProfile(
        name="enterprise-doc-default",
        trust_hierarchy=["system_of_record", "signed_document", "ocr_text", "llm_inference"],
        ambiguity_policy="surface_explicitly",
        fallback_alignment_strategy="identity_then_strict_value",
        comparability_policy=ComparabilityPolicy(
            require_same_worldview_profile=True,
            require_same_test_set_version=True,
            require_same_alignment_strategy=True,
            allow_fallback_alignment_when_identity_missing=False,
        ),
        escalation_policy={"error": "page-oncall", "warning": "queue-review"},
        accountability=AccountabilityMapping(
            owner_by_class={
                "missing_field": "team:parser",
                "value_mismatch": "team:model-eval",
                "missing_truth_row": "team:data-quality",
                "unknown_error_class": "team:world-governance",
            }
        ),
    )
