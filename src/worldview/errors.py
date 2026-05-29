"""Domain and enforcement errors for the world view platform."""


class WorldViewError(Exception):
    """Base error for world view SDK and platform operations."""


class OntologyViolation(WorldViewError):
    """Raised when ontology or relation constraints are violated."""


class TransitionViolation(WorldViewError):
    """Raised when a state transition is not allowed by ASM rules."""


class EvidenceViolation(WorldViewError):
    """Raised when evidence requirements are not satisfied."""
