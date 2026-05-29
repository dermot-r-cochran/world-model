"""Runtime errors for enforced world model semantics."""


class WorldRuntimeError(Exception):
    """Base error for runtime operations."""


class IdentityError(WorldRuntimeError):
    """Raised when identity rules are violated."""


class TransitionError(WorldRuntimeError):
    """Raised when a transition violates allowed lifecycle rules."""


class EvidenceError(WorldRuntimeError):
    """Raised when evidence requirements are not satisfied."""


class InvariantError(WorldRuntimeError):
    """Raised when invariants are violated."""
