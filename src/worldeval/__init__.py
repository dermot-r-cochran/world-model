"""Evaluation package for run scoring, mismatch classification, and comparability decisions."""

from .models import ComparabilityDecision, EvaluationResult, Mismatch
from .service import EvaluationService

__all__ = ["Mismatch", "EvaluationResult", "ComparabilityDecision", "EvaluationService"]
