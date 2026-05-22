"""Tests for the PDDL-backed neuro-symbolic planner."""
from __future__ import annotations

from pathlib import Path
from random import Random
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from mm_retail_robot.assistant import NeuroSymbolicRetailAssistant
from mm_retail_robot.catalog import load_catalog
from mm_retail_robot.pddl import breadth_first_plan, initial_atoms, write_pddl_problem
from mm_retail_robot.user_state import infer_interaction_state


def test_budget_sensitive_user_gets_budget_plan(tmp_path: Path) -> None:
    catalog = load_catalog(REPO_ROOT / "data" / "product_catalog.json")
    state = infer_interaction_state(
        "I need comfortable trousers under 60 euros. Please do not show premium options.",
        rng=Random(1),
        budget_extraction_error_rate=0.0,
    )
    plan = breadth_first_plan(state, catalog)
    assert any(step.startswith("recommend-budget-trousers") for step in plan)
    assert not any(step.startswith("recommend-premium-trousers") for step in plan)


def test_pddl_files_are_written(tmp_path: Path) -> None:
    catalog = load_catalog(REPO_ROOT / "data" / "product_catalog.json")
    state = infer_interaction_state("comfortable trousers under 60 euros", rng=Random(1), budget_extraction_error_rate=0.0)
    domain_path, problem_path = write_pddl_problem(state, catalog, tmp_path)
    assert domain_path.exists()
    assert problem_path.exists()
    assert "retail-recommendation" in domain_path.read_text(encoding="utf-8")
    assert "under-budget" in problem_path.read_text(encoding="utf-8")


def test_neurosymbolic_recommendation_respects_budget(tmp_path: Path) -> None:
    catalog = load_catalog(REPO_ROOT / "data" / "product_catalog.json")
    state = infer_interaction_state("I need comfortable trousers under 60 euros", rng=Random(1), budget_extraction_error_rate=0.0)
    assistant = NeuroSymbolicRetailAssistant(catalog, pddl_output_dir=tmp_path, rng=Random(2))
    result = assistant.recommend(state)
    assert result.product.price <= 60
    assert result.pddl_problem_path is not None
    assert len(result.plan) > 0
