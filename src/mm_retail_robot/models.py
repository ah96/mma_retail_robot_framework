"""Core dataclasses for the retail robot prototype.

The module keeps the representation intentionally compact so that the
implementation can be understood and reproduced in a workshop paper.  The
symbolic state is later compiled into a small PDDL problem.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class Product:
    """A product in the retail catalogue."""

    id: str
    name: str
    price: float
    style: str
    comfort: int
    available: bool
    premium: bool
    promotion: bool


@dataclass
class MentalModel:
    """A compact symbolic approximation of the customer's mental model."""

    budget: Optional[float] = None
    budget_sensitive: bool = False
    comfort_priority: bool = False
    intended_use: str = "everyday"
    uncertain: bool = False
    upsell_rejected: bool = False
    prefers_low_pressure: bool = True


@dataclass
class InteractionState:
    """Verified interaction state used by the symbolic layer."""

    user_id: str = "customer1"
    mental_model: MentalModel = field(default_factory=MentalModel)
    viewed_products: Set[str] = field(default_factory=set)
    rejected_products: Set[str] = field(default_factory=set)
    commercial_disclosures: Set[str] = field(default_factory=set)
    extracted_budget_correctly: bool = True


@dataclass
class RecommendationResult:
    """Output of either the LLM-only or neuro-symbolic policy."""

    condition: str
    product: Product
    response: str
    explanation: str
    plan: List[str] = field(default_factory=list)
    pddl_domain_path: Optional[str] = None
    pddl_problem_path: Optional[str] = None
    metadata: Dict[str, object] = field(default_factory=dict)
