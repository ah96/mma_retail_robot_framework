# Mental-Model-Aware Retail Robot Prototype

This repository contains a lightweight prototype for comparing an **LLM-only retail robot** against a **neuro-symbolic retail robot** in a trouser-recommendation scenario.

The implementation is designed for the ICSR 2026 ASIMOV workshop paper.  It is intentionally small, reproducible, and inspectable.

## What is implemented?

The repository contains two conditions:

1. **LLM-only baseline**
   - Selects products directly from the conversational context.
   - Sometimes respects budget and sometimes gives partial explanations.
   - Does not verify recommendations against an explicit symbolic interaction state.

2. **Neuro-symbolic condition with PDDL compilation**
   - Extracts a compact symbolic mental model from the user request, covering both economic and non-economic parameters (see [Mental model](#mental-model) below).
   - Compiles the interaction state and catalogue into PDDL files:
     - `generated_pddl/domain.pddl`
     - `generated_pddl/problem.pddl`
   - Generates a short symbolic interaction plan using a reproducible lightweight STRIPS planner over the generated PDDL domain.
   - Grounds the final recommendation and explanation in the symbolic plan.
   - Supports a multi-turn **contestability loop** in which the user can correct the inferred mental model and the system re-plans accordingly (see [Contestability loop](#contestability-loop)).

The current planner is deliberately small and embedded for reproducibility.  The generated PDDL files can be inspected or later passed to an external planner such as Fast Downward or pyperplan.

## Mental model

`MentalModel` (defined in `src/mm_retail_robot/models.py`) captures all inferred customer preferences.  Every field is compiled into a typed PDDL predicate by `pddl.initial_atoms()` so the symbolic layer has a complete view of the customer state.

| Field | PDDL predicate | Notes |
|-------|----------------|-------|
| `budget` | `under-budget` | Hard price ceiling extracted from the utterance |
| `budget_sensitivity` | `budget-sensitive` | True when price is an explicit concern |
| `budget_flexibility` | `budget-flexible` + `near-budget` | Non-zero when hedging language is detected ("a bit over", "around", "flexible"); enables `recommend-flex-budget-trousers` |
| `comfort_priority` | `comfort-priority` | Triggers the comfort-aware recommendation action |
| `intended_use == "formal"` | `formal-use` | Triggers `recommend-formal-trousers` |
| `uncertain` | `uncertain` | Triggers `offer-comparison` instead of `offer-alternative` |
| `upsell_rejected` | `upsell-rejected` | Blocks `recommend-premium-trousers` |
| `prefers_low_pressure` | `low-pressure` | Softens the phrasing of alternative suggestions |

## PDDL domain actions

The domain (`generated_pddl/domain.pddl`) contains the following actions, explored in priority order by the planner:

| Action | Fires when |
|--------|-----------|
| `request-budget-clarification` | Neural extraction layer failed to parse the budget; blocks all recommend actions until resolved |
| `recommend-budget-trousers` | User stated a budget and a comfort preference; product is within budget |
| `recommend-any-budget-trousers` | User stated a budget but no comfort/formal preference; product is within budget |
| `recommend-flex-budget-trousers` | User expressed budget flexibility; product is within the extended range |
| `recommend-formal-trousers` | User specified a formal or interview context |
| `recommend-premium-trousers` | User has not rejected upsell and is not budget-sensitive; commercial intent disclosed first |
| `offer-alternative` | Recommendation made; user is not uncertain |
| `offer-comparison` | Recommendation made; user expressed uncertainty |
| `explain-recommendation` | A product has been recommended |
| `disclose-commercial-intent` | Product is premium; must precede any premium recommendation |

## Error handling for upstream extraction failures

When the neural dialogue layer fails to extract the budget from the user utterance (simulated via `budget_extraction_error_rate`), the `clarification-needed` predicate is asserted in the PDDL init state.  All `recommend-*` actions guard on `not (clarification-needed ?u)`, so the planner is forced to schedule `request-budget-clarification` before any product recommendation.  The response generation layer detects this step and produces a clarification request instead of committing to a product.  The `RecommendationResult.metadata["clarification_needed"]` flag surfaces this to downstream callers.

## Contestability loop

`ContestabilityEngine` (defined in `src/mm_retail_robot/contestability.py`) implements the multi-turn correction loop described in the paper.

```python
from mm_retail_robot.contestability import ContestabilityEngine
from mm_retail_robot.catalog import load_catalog

catalog = load_catalog("data/product_catalog.json")
engine = ContestabilityEngine(catalog)

turns = engine.run(
    "I need trousers under 60 euros",
    corrections=["Actually, for a job interview — formal is important"],
)

for i, turn in enumerate(turns):
    print(f"Turn {i}: {turn.result.plan}")
    print(f"  => {turn.result.response}")
```

Each correction utterance is merged field-by-field into the prior mental model: only fields that the correction explicitly changes are overwritten; everything else (e.g. the budget from turn 0) is inherited.  This models the paper's claim that users can selectively override an inferred mental model when a constraint mismatch occurs.

**Example trace:**

```text
Turn 0: utterance = "I need trousers under 60 euros"
  plan: [recommend-any-budget-trousers customer1 classic_chino, offer-alternative customer1]
  mental model: intended_use='everyday', budget=60.0

Turn 1: utterance = "Actually, for a job interview — formal is important"
  plan: [recommend-formal-trousers customer1 classic_chino, offer-alternative customer1]
  mental model: intended_use='formal', budget=60.0  ← budget preserved from turn 0
```

## Scalability

`breadth_first_plan()` accepts a `max_candidates` parameter (default 20).  When the catalogue exceeds that threshold, `_filter_catalog_for_planning()` pre-selects the K most relevant products by scoring each on budget fit, comfort match, style match, and upsell-rejection penalty.  This bounds the planner's action space to O(K) regardless of catalogue size and reduces the BFS branching factor from O(N) to O(K).  Actions are also sorted by type priority so the most likely paths are explored first, further reducing average states visited.

## Repository structure

```text
mma_retail_robot_framework/
├── README.md
├── requirements.txt
├── data/
│   └── product_catalog.json
├── generated_pddl/
│   ├── domain.pddl
│   └── problem.pddl
├── results/
├── scripts/
│   ├── run_demo.py
│   └── run_simulated_evaluation.py
├── src/
│   └── mm_retail_robot/
│       ├── assistant.py       — LLMOnlyRetailAssistant, NeuroSymbolicRetailAssistant
│       ├── catalog.py         — product catalogue loader
│       ├── contestability.py  — ContestabilityEngine, ContestabilityTurn
│       ├── evaluator.py       — simulation and metrics aggregation
│       ├── explanation.py     — plan-grounded response generation
│       ├── models.py          — MentalModel, InteractionState, RecommendationResult
│       ├── pddl.py            — PDDL compilation, STRIPS planner, scalability filter
│       └── user_state.py      — utterance-to-state extraction
└── tests/
    └── test_pddl_planner.py
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run one demonstration

```bash
python scripts/run_demo.py \
  --utterance "I need comfortable trousers for everyday wear, preferably under 60 euros. Please do not show premium options."
```

The neuro-symbolic condition will print a symbolic plan such as:

```text
1. recommend-budget-trousers customer1 classic_chino
2. offer-alternative customer1
```

and will write the generated PDDL files to `generated_pddl/`.

**Flex-budget utterance:**

```bash
python scripts/run_demo.py \
  --utterance "I need comfortable trousers, around 60 euros — a bit over is fine."
```

## Run the simulated evaluation

```bash
python3 scripts/run_simulated_evaluation.py --n-users 200 --output-dir results
```

Outputs:

```text
results/simulated_trials.csv
results/condition_summary.csv
results/rate_metrics_noisy_pddl.png
results/rate_metrics_noisy_pddl.pdf
results/mean_price_noisy_pddl.png
results/mean_price_noisy_pddl.pdf
```

## Run the tests

```bash
python -m pytest tests/ -v
```

The test suite covers: budget-constraint enforcement, PDDL file generation, flex-budget extraction and planning, non-economic predicate compilation, contestability loop state merging, upstream clarification handling, and catalogue pre-filtering.

## Interpretation

The simulation is an implementation-level sanity check, not a user study.  It tests whether symbolic planning and verification reduce constraint violations and improve grounded explanations in a toy retail domain.

## Academic use

The prototype should be described as a PDDL-backed neuro-symbolic prototype with an embedded lightweight STRIPS planner.  It is compatible with external PDDL planners, but the included planner is used to keep the workshop artifact self-contained.
