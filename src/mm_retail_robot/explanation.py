"""Explanation generation grounded in symbolic plan traces."""
from __future__ import annotations

from random import Random
from typing import Sequence

from .models import InteractionState, Product


def generate_grounded_response(
    product: Product,
    state: InteractionState,
    plan: Sequence[str],
    *,
    rng: Random | None = None,
    explanation_omission_rate: float = 0.08,
) -> tuple[str, str]:
    """Generate a natural-language response from a product and symbolic plan.

    The response remains template-based so that the paper can claim faithful
    grounding in symbolic state rather than hidden LLM reasoning.  A small
    omission rate simulates realistic surface-generation failures.
    """
    rng = rng or Random(0)
    model = state.mental_model

    reasons = []
    if model.comfort_priority and product.comfort >= 4:
        reasons.append("you said comfort is important")
    if model.budget is not None and product.price <= model.budget:
        reasons.append(f"it is within your budget of {model.budget:.0f} euros")
    if product.style == model.intended_use:
        reasons.append(f"it matches your intended {model.intended_use} use")
    if product.premium and any(step.startswith("disclose-commercial-intent") for step in plan):
        reasons.append("it is a premium item, so I am explicitly disclosing that before recommending it")

    if rng.random() < explanation_omission_rate and reasons:
        # Simulate an imperfect surface explanation while keeping the selected
        # recommendation constrained by the symbolic layer.
        reasons = reasons[:-1]

    if not reasons:
        reasons = ["it satisfies the current symbolic recommendation constraints"]

    explanation = "I recommend this item because " + ", ".join(reasons) + "."
    response = (
        f"I suggest {product.name}. {explanation} "
        "I can also show cheaper, more formal, or more casual alternatives if you want."
    )
    return response, explanation


def generate_llm_only_response(product: Product, *, budget_aware: bool, contestable: bool) -> tuple[str, str]:
    """Generate a baseline LLM-only style response.

    This baseline is intentionally stochastic: sometimes it gives a reasonable
    explanation, but it is not constrained by an explicit symbolic state.
    """
    fragments = [f"I think {product.name} would be a great choice for you"]
    if budget_aware:
        fragments.append("it appears to fit what you said about price and comfort")
    else:
        fragments.append("it is stylish, comfortable, and popular with customers")
    if contestable:
        fragments.append("I can also show alternatives")
    response = ". ".join(fragments) + "."
    return response, ". ".join(fragments[1:]) + "."
