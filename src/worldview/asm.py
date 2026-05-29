"""ASM definitions: ontology, transitions, and invariant policy."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RelationType(BaseModel):
    """Defines a typed relation between source and target entity types."""

    name: str
    source_type: str
    target_type: str


class TransitionRule(BaseModel):
    """Defines allowed state transitions for one entity type."""

    entity_type: str
    from_state: str
    to_state: str


class WorldASM(BaseModel):
    """Architectural Specification Model for world view semantics."""

    entity_types: set[str] = Field(default_factory=set)
    relation_types: list[RelationType] = Field(default_factory=list)
    transition_rules: list[TransitionRule] = Field(default_factory=list)
    require_evidence_for_claims: bool = True

    def is_known_entity_type(self, entity_type: str) -> bool:
        return entity_type in self.entity_types

    def is_allowed_relation(self, relation_name: str, source_type: str, target_type: str) -> bool:
        return any(
            r.name == relation_name and r.source_type == source_type and r.target_type == target_type
            for r in self.relation_types
        )

    def is_allowed_transition(self, entity_type: str, from_state: str, to_state: str) -> bool:
        return any(
            r.entity_type == entity_type and r.from_state == from_state and r.to_state == to_state
            for r in self.transition_rules
        )


def default_business_asm() -> WorldASM:
    """Default ASM for document extraction and evaluation workflows."""

    return WorldASM(
        entity_types={
            "document",
            "section",
            "extracted_row",
            "test_set",
            "evaluation_run",
            "error_class",
            "owner_team",
            "model_version",
            "parser_version",
            "prompt_version",
        },
        relation_types=[
            RelationType(name="contains", source_type="document", target_type="section"),
            RelationType(name="supports", source_type="section", target_type="extracted_row"),
            RelationType(name="classified_as", source_type="extracted_row", target_type="error_class"),
            RelationType(name="owned_by", source_type="error_class", target_type="owner_team"),
        ],
        transition_rules=[
            TransitionRule(entity_type="evaluation_run", from_state="created", to_state="running"),
            TransitionRule(entity_type="evaluation_run", from_state="running", to_state="completed"),
            TransitionRule(entity_type="document", from_state="draft", to_state="ingested"),
            TransitionRule(entity_type="document", from_state="ingested", to_state="processed"),
        ],
        require_evidence_for_claims=True,
    )
