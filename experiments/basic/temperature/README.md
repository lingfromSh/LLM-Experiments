# Temperature

Systematic evaluation of how LLM temperature settings affect performance across different task types.

## Goal

Determine optimal temperature ranges for:
- **Rigorous tasks** (math proofs, code generation, factual QA) → expect low temp
- **Creative tasks** (writing, brainstorming) → expect higher temp
- **Translation** → expect low temp (fidelity matters)

## Quick Start

```bash
# 1. Make sure your local LLM is running on localhost:1234
# 2. Run the experiment
cd /path/to/MyLLMEval
python -m experiments.basic.temperature.runner

# 3. Generate report
python -m experiments.basic.temperature.report
```

## How It Works

1. **Runner** iterates over `temperatures × datasets`
2. For each combination, calls the LLM with that temperature
3. Scores each response using the appropriate method:
   - `exact_match` — extracts answer, compares to ground truth
   - `code_exec` — runs test cases against generated code
   - `geval` — LLM-as-judge via deepeval with custom rubrics
4. Results saved as structured JSON in `results/`
5. **Report** generates Markdown tables + CSV in `reports/`

## Configuration

Edit `experiments/config.py` to change:
- `TEMPERATURES` — temperature values to sweep
- `DATASET_CONFIG` — which datasets to include
- `models.json` — model endpoint definitions

## Structure

```
experiments/
├── config.py                          # Shared config (models, datasets, paths)
├── models.json                        # Model endpoint definitions
└── basic/
    └── temperature/
        ├── README.md                  # This file
        ├── metrics.py                 # Scoring: exact_match, code_exec, geval
        ├── runner.py                  # Experiment runner
        ├── report.py                  # Report generator
        ├── results/                   # Raw JSON results (gitignored)
        └── reports/                   # Generated reports
```
