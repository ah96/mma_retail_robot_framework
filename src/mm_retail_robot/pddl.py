"""PDDL compilation and lightweight STRIPS planning.

The current prototype now uses actual PDDL files as an intermediate symbolic
representation.  For reproducibility, this module also contains a very small
STRIPS planner tailored to the generated domain.  The generated domain and
problem files can be inspected, committed to GitHub, or replaced by calls to an
external planner in future work.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Sequence, Set, Tuple

from .models import InteractionState, Product


DOMAIN_TEXT = """(define (domain retail-recommendation)
  (:requirements :strips :typing :negative-preconditions)
  (:types customer product)
  (:predicates
    (customer ?u - customer)
    (product ?p - product)
    (trousers ?p - product)
    (available ?p - product)
    (premium-item ?p - product)
    (comfort-priority ?u - customer)
    (budget-sensitive ?u - customer)
    (under-budget ?p - product ?u - customer)
    (upsell-rejected ?u - customer)
    (commercial-intent-disclosed ?p - product)
    (recommended ?u - customer ?p - product)
    (recommendation-made ?u - customer)
    (explained ?u - customer ?p - product)
    (alternative-offered ?u - customer)
  )

  (:action disclose-commercial-intent
    :parameters (?u - customer ?p - product)
    :precondition (and (customer ?u) (product ?p) (premium-item ?p))
    :effect (and (commercial-intent-disclosed ?p))
  )

  (:action recommend-budget-trousers
    :parameters (?u - customer ?p - product)
    :precondition (and
      (customer ?u)
      (product ?p)
      (trousers ?p)
      (available ?p)
      (comfort-priority ?u)
      (under-budget ?p ?u)
    )
    :effect (and (recommended ?u ?p) (recommendation-made ?u))
  )

  (:action recommend-premium-trousers
    :parameters (?u - customer ?p - product)
    :precondition (and
      (customer ?u)
      (product ?p)
      (trousers ?p)
      (available ?p)
      (premium-item ?p)
      (not (budget-sensitive ?u))
      (not (upsell-rejected ?u))
      (commercial-intent-disclosed ?p)
    )
    :effect (and (recommended ?u ?p) (recommendation-made ?u))
  )

  (:action explain-recommendation
    :parameters (?u - customer ?p - product)
    :precondition (and (recommended ?u ?p))
    :effect (and (explained ?u ?p))
  )

  (:action offer-alternative
    :parameters (?u - customer)
    :precondition (and (recommendation-made ?u))
    :effect (and (alternative-offered ?u))
  )
)
"""

Atom = Tuple[str, ...]


@dataclass(frozen=True)
class GroundAction:
    """A grounded STRIPS action used by the lightweight planner."""

    name: str
    positive_preconditions: FrozenSet[Atom]
    negative_preconditions: FrozenSet[Atom]
    add_effects: FrozenSet[Atom]
    delete_effects: FrozenSet[Atom] = frozenset()

    def applicable(self, state: FrozenSet[Atom]) -> bool:
        """Return True iff the action is applicable in ``state``."""
        return self.positive_preconditions.issubset(state) and self.negative_preconditions.isdisjoint(state)

    def apply(self, state: FrozenSet[Atom]) -> FrozenSet[Atom]:
        """Apply the STRIPS action to a state."""
        return frozenset((set(state) - set(self.delete_effects)) | set(self.add_effects))


def product_object(product: Product) -> str:
    """Return a PDDL-safe object name."""
    return product.id.replace("-", "_")


def atom_to_pddl(atom: Atom) -> str:
    """Format an atom tuple as PDDL syntax."""
    return "(" + " ".join(atom) + ")"


def initial_atoms(state: InteractionState, catalog: Sequence[Product]) -> Set[Atom]:
    """Compile the current Python state into symbolic atoms."""
    user = state.user_id
    model = state.mental_model
    atoms: Set[Atom] = {("customer", user)}

    if model.comfort_priority:
        atoms.add(("comfort-priority", user))
    if model.budget_sensitive:
        atoms.add(("budget-sensitive", user))
    if model.upsell_rejected:
        atoms.add(("upsell-rejected", user))

    for product in catalog:
        pid = product_object(product)
        atoms.update({("product", pid), ("trousers", pid)})
        if product.available:
            atoms.add(("available", pid))
        if product.premium:
            atoms.add(("premium-item", pid))
        if pid in state.commercial_disclosures:
            atoms.add(("commercial-intent-disclosed", pid))
        if model.budget is not None and product.price <= model.budget:
            atoms.add(("under-budget", pid, user))

    return atoms


def goal_atoms(user_id: str = "customer1") -> Set[Atom]:
    """Goal atoms for the prototype interaction plan."""
    return {("recommendation-made", user_id), ("alternative-offered", user_id)}


def write_pddl_problem(
    state: InteractionState,
    catalog: Sequence[Product],
    output_dir: str | Path,
    problem_name: str = "retail_problem",
) -> tuple[Path, Path]:
    """Write PDDL domain and problem files to disk.

    Returns
    -------
    tuple[Path, Path]
        Paths to ``domain.pddl`` and ``problem.pddl``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    domain_path = out / "domain.pddl"
    problem_path = out / "problem.pddl"
    domain_path.write_text(DOMAIN_TEXT, encoding="utf-8")

    user = state.user_id
    products = " ".join(product_object(p) for p in catalog)
    init = "\n    ".join(sorted(atom_to_pddl(atom) for atom in initial_atoms(state, catalog)))
    goals = "\n      ".join(sorted(atom_to_pddl(atom) for atom in goal_atoms(user)))

    problem = f"""(define (problem {problem_name})
  (:domain retail-recommendation)
  (:objects
    {user} - customer
    {products} - product
  )
  (:init
    {init}
  )
  (:goal (and
      {goals}
  ))
)
"""
    problem_path.write_text(problem, encoding="utf-8")
    return domain_path, problem_path


def ground_actions(state: InteractionState, catalog: Sequence[Product]) -> List[GroundAction]:
    """Ground the generated retail PDDL domain for the finite catalogue."""
    user = state.user_id
    actions: List[GroundAction] = []

    for product in catalog:
        pid = product_object(product)
        actions.append(
            GroundAction(
                name=f"disclose-commercial-intent {user} {pid}",
                positive_preconditions=frozenset({("customer", user), ("product", pid), ("premium-item", pid)}),
                negative_preconditions=frozenset(),
                add_effects=frozenset({("commercial-intent-disclosed", pid)}),
            )
        )
        actions.append(
            GroundAction(
                name=f"recommend-budget-trousers {user} {pid}",
                positive_preconditions=frozenset({
                    ("customer", user),
                    ("product", pid),
                    ("trousers", pid),
                    ("available", pid),
                    ("comfort-priority", user),
                    ("under-budget", pid, user),
                }),
                negative_preconditions=frozenset(),
                add_effects=frozenset({("recommended", user, pid), ("recommendation-made", user)}),
            )
        )
        actions.append(
            GroundAction(
                name=f"recommend-premium-trousers {user} {pid}",
                positive_preconditions=frozenset({
                    ("customer", user),
                    ("product", pid),
                    ("trousers", pid),
                    ("available", pid),
                    ("premium-item", pid),
                    ("commercial-intent-disclosed", pid),
                }),
                negative_preconditions=frozenset({("budget-sensitive", user), ("upsell-rejected", user)}),
                add_effects=frozenset({("recommended", user, pid), ("recommendation-made", user)}),
            )
        )
        actions.append(
            GroundAction(
                name=f"explain-recommendation {user} {pid}",
                positive_preconditions=frozenset({("recommended", user, pid)}),
                negative_preconditions=frozenset(),
                add_effects=frozenset({("explained", user, pid)}),
            )
        )

    actions.append(
        GroundAction(
            name=f"offer-alternative {user}",
            positive_preconditions=frozenset({("recommendation-made", user)}),
            negative_preconditions=frozenset(),
            add_effects=frozenset({("alternative-offered", user)}),
        )
    )
    return actions


def breadth_first_plan(
    state: InteractionState,
    catalog: Sequence[Product],
    max_depth: int = 5,
) -> List[str]:
    """Find a short interaction plan with breadth-first search.

    The search is intentionally small because the workshop domain contains only a
    few products and short interaction plans.
    """
    init = frozenset(initial_atoms(state, catalog))
    goals = goal_atoms(state.user_id)
    actions = ground_actions(state, catalog)

    frontier: List[tuple[FrozenSet[Atom], List[str]]] = [(init, [])]
    visited = {init}

    while frontier:
        current_state, current_plan = frontier.pop(0)
        if goals.issubset(current_state):
            return current_plan
        if len(current_plan) >= max_depth:
            continue
        for action in actions:
            if action.applicable(current_state):
                next_state = action.apply(current_state)
                if next_state not in visited:
                    visited.add(next_state)
                    frontier.append((next_state, current_plan + [action.name]))
    return []


def recommended_product_from_plan(plan: Sequence[str], catalog: Sequence[Product]) -> Product | None:
    """Extract the recommended product from a generated plan."""
    product_by_id: Dict[str, Product] = {product_object(product): product for product in catalog}
    for step in plan:
        if step.startswith("recommend-"):
            pid = step.split()[-1]
            return product_by_id.get(pid)
    return None
