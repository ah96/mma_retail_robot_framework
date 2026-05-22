"""Simple user-state extraction for the retail scenario.

This is deliberately lightweight: the goal of the prototype is to test the
architecture, not to build a robust NLU module.  The extraction function supports
controlled noise so that the neuro-symbolic condition is not an unrealistic
oracle.
"""
from __future__ import annotations

import re
from random import Random

from .models import InteractionState, MentalModel


def infer_interaction_state(
    utterance: str,
    *,
    rng: Random | None = None,
    budget_extraction_error_rate: float = 0.03,
) -> InteractionState:
    """Infer a symbolic interaction state from a user utterance.

    Parameters
    ----------
    utterance:
        User request, e.g., "comfortable trousers under 60 euros".
    rng:
        Optional random generator for reproducible extraction noise.
    budget_extraction_error_rate:
        Probability that the system fails to extract the budget, even when it is
        present.  This simulates realistic upstream NLU imperfections.
    """
    rng = rng or Random(0)
    text = utterance.lower()

    budget_match = re.search(r"(?:under|below|less than|up to|maximum|max|budget)[^0-9]*(\d+)", text)
    budget = float(budget_match.group(1)) if budget_match else None
    extracted_budget_correctly = True

    if budget is not None and rng.random() < budget_extraction_error_rate:
        budget = None
        extracted_budget_correctly = False

    model = MentalModel(
        budget=budget,
        budget_sensitive=(budget is not None) or any(token in text for token in ["cheap", "budget", "affordable"]),
        comfort_priority=any(token in text for token in ["comfortable", "comfort", "relaxed"]),
        intended_use="formal" if "interview" in text or "formal" in text else "everyday",
        uncertain=any(token in text for token in ["not sure", "maybe", "unsure"]),
        upsell_rejected=any(token in text for token in ["no premium", "not premium", "do not show premium", "no expensive"]),
        prefers_low_pressure=True,
    )
    return InteractionState(mental_model=model, extracted_budget_correctly=extracted_budget_correctly)
