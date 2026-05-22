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
   - Extracts a compact symbolic mental model from the user request.
   - Compiles the interaction state and catalogue into PDDL files:
     - `generated_pddl/domain.pddl`
     - `generated_pddl/problem.pddl`
   - Generates a short symbolic interaction plan using a reproducible lightweight STRIPS planner over the generated PDDL-style domain.
   - Grounds the final recommendation and explanation in the symbolic plan.

The current planner is deliberately small and embedded for reproducibility.  The generated PDDL files can be inspected or later passed to an external planner such as Fast Downward or pyperplan.

## Repository structure

```text
mm_retail_robot_framework_v3/
├── README.md
├── requirements.txt
├── data/
│   └── product_catalog.json
├── generated_pddl/
├── results/
├── scripts/
│   ├── run_demo.py
│   └── run_simulated_evaluation.py
├── src/
│   └── mm_retail_robot/
│       ├── assistant.py
│       ├── catalog.py
│       ├── evaluator.py
│       ├── explanation.py
│       ├── models.py
│       ├── pddl.py
│       └── user_state.py
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

## Run the simulated evaluation

```bash
python3 scripts/run_simulated_evaluation.py --n-users 200 --output-dir results
```

Outputs:

```text
results/simulated_trials.csv
results/condition_summary.csv
results/metric_comparison_noisy_pddl.png
results/metric_comparison_noisy_pddl.pdf
```

## Interpretation

The simulation is an implementation-level sanity check, not a user study.  It tests whether symbolic planning and verification reduce constraint violations and improve grounded explanations in a toy retail domain.

## Academic use

The prototype should be described as a PDDL-backed neuro-symbolic prototype with an embedded lightweight STRIPS planner.  It is compatible with external PDDL planners, but the included planner is used to keep the workshop artifact self-contained.
