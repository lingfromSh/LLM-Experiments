# 🔬 LLM Experiments

> A systematic evaluation framework for LLMs and Agents — from temperature sweeps to cross-model Cartesian product benchmarks.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-black.svg)](https://github.com/astral-sh/uv)

---

## The Problem

Everyone benchmarks LLMs. Almost nobody does it rigorously.

Leaderboards optimize for cherry-picked tasks. Production performance depends on interactions you never tested — temperature × task type × model × prompt strategy. You ship v1, tweak a hyperparameter, and watch quality silently degrade because your "eval" was a vibe check.

**LLM Experiments** exists to fix this. It's a reproducible evaluation harness that treats LLM assessment the way serious engineering treats performance testing: systematic, observable, and exhaustive.

---

## What This Is

A Python framework for running controlled experiments across LLMs and agents, with:

- **Temperature sweep experiments** — measure how sampling temperature affects quality across 7 task categories
- **Multi-model comparison** — Cartesian product evaluation across arbitrary model configurations
- **Agent evaluation** — extend beyond single-turn QA to multi-step agent workflows
- **LLM-as-Judge scoring** — calibrated GEval metrics with configurable rubrics
- **Observability built-in** — Arize Phoenix tracing for every inference, every judgment
- **Reproducible by default** — declarative configs, versioned datasets, deterministic execution

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Experiment Runner                      │
│  (pytest + deepeval + litellm unified interface)         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │  Models   │  │ Datasets │  │   Scoring Pipeline   │  │
│  │           │  │          │  │                      │  │
│  │ models.   │  │ registry │  │  exact_match         │  │
│  │ json      │  │ .yaml →  │  │  code_exec           │  │
│  │ (litellm) │  │ JSONL    │  │  GEval (LLM judge)   │  │
│  └──────────┘  └──────────┘  └──────────────────────┘  │
│                                                          │
├─────────────────────────────────────────────────────────┤
│              Observability Layer                          │
│         Arize Phoenix (traces, spans, metrics)           │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision                       | Rationale                                                                                      |
| ------------------------------ | ---------------------------------------------------------------------------------------------- |
| **LiteLLM as model interface** | One API for OpenAI, Anthropic, local (vLLM, Ollama, LM Studio), any OpenAI-compatible endpoint |
| **DeepEval as metric engine**  | Production-grade GEval implementation with built-in caching and model abstraction              |
| **pytest as runner**           | Leverage existing ecosystem — parallelism, filtering, CI integration, rich reporting           |
| **JSONL datasets**             | Streaming-friendly, git-diffable, no database dependency                                       |
| **Arize Phoenix for tracing**  | Open-source, local-first, OpenTelemetry-compatible. No vendor lock-in                          |

---

## Quick Start

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- At least one LLM endpoint (local or remote)

### Installation

```bash
# Clone the repo
git clone https://github.com/<your-org>/llm-experiments.git
cd llm-experiments

# Install dependencies (uv)
uv sync

# Or with pip
pip install -e .
```

### Configure Models

Copy the example config and define your models:

```bash
cp models.json.example models.json
```

```jsonc
// models.json
{
  "default": {
    "model": "openai/gpt-4o-mini",
    "api_key": "sk-...",
    "api_base": "https://api.openai.com/v1",
  },
  "claude": {
    "model": "anthropic/claude-sonnet-4-20250514",
    "api_key": "sk-ant-...",
  },
  "local": {
    "model": "openai/your-local-model",
    "api_key": "no_need_any_key",
    "api_base": "http://localhost:1234/v1",
  },
  "judge": {
    "model": "openai/gpt-4o",
    "api_key": "sk-...",
    "api_base": "https://api.openai.com/v1",
  },
}
```

The `judge` key defines which model scores subjective tasks via GEval. Separate it from your test models to avoid self-evaluation bias.

### Fetch Datasets

```bash
# Download all benchmark datasets
python datasets/scripts/fetch_datasets.py

# Download a specific dataset
python datasets/scripts/fetch_datasets.py --dataset gsm8k

# List available datasets
python datasets/scripts/fetch_datasets.py --list
```

### Run Your First Experiment

```bash
# Run a basic correctness test
pytest experiments/example.py -v

# Run temperature sweep on math tasks
pytest experiments/basic/ -v --test-llm-model default

# Compare two models head-to-head
pytest experiments/basic/ -v --test-llm-model default
pytest experiments/basic/ -v --test-llm-model claude
```

---

## Usage Guide

### Experiment Structure

```
experiments/
├── conftest.py          # CLI options, shared fixtures
├── config.py            # Model loading, dataset config, paths
├── example.py           # Minimal example — start here
└── basic/               # Temperature sweep experiments
```

### Writing an Experiment

Every experiment is a pytest test function. The framework handles model routing, dataset loading, and metric computation:

```python
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, SingleTurnParams
from deepeval.metrics import GEval
from deepeval.models import LiteLLMModel
from experiments.config import get_model

def test_my_experiment():
    # 1. Configure the model under test
    model_cfg = get_model("default")
    target_model = LiteLLMModel(
        model=model_cfg["model"],
        api_key=model_cfg["api_key"],
        api_base=model_cfg.get("api_base"),
    )

    # 2. Define your metric
    metric = GEval(
        name="Correctness",
        criteria="Is the output factually correct?",
        evaluation_params=[
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
        model=target_model,
    )

    # 3. Define test cases
    test_case = LLMTestCase(
        input="What is the capital of France?",
        actual_output="Paris",
        expected_output="Paris",
    )

    # 4. Assert
    assert_test(test_case, [metric])
```

### Temperature Sweep

The core experiment type. Measures how sampling temperature affects output quality across task categories:

```bash
# Temperatures tested: [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
# Categories: math, coding, factual, reasoning, writing, creative_writing, translation

pytest experiments/basic/ -v -s
```

Each category has a pre-defined hypothesis (e.g., "low temperature should perform best on math") and calibrated GEval criteria. Results let you validate or refute these assumptions per model.

### Dataset Format

All datasets use a unified JSONL schema:

```json
{
  "id": "gsm8k_001",
  "category": "math",
  "input": "Janet has 5 apples...",
  "expected_output": "10",
  "metadata": {
    "difficulty": "easy",
    "source": "gsm8k",
    "scoring": "exact_match"
  }
}
```

Three scoring methods:

| Method        | Tasks                                   | Mechanism                                           |
| ------------- | --------------------------------------- | --------------------------------------------------- |
| `exact_match` | Math, Reasoning                         | Regex-extract final answer, compare to ground truth |
| `code_exec`   | Coding                                  | Execute generated code against test cases           |
| `geval`       | Factual, Writing, Translation, Creative | LLM-as-judge with structured rubric                 |

### Observability

Arize Phoenix traces every inference call — both target model and judge model:

```bash
# Start Phoenix UI (opens at http://localhost:6006)
python -m phoenix.server.main serve

# Traces are automatically exported via OpenTelemetry
# View: prompt → completion → latency → token usage → judge scores
```

This is not optional instrumentation. When your eval says "model A beats model B," Phoenix lets you inspect _why_ — which specific examples flipped the result, where the judge disagreed, what the temperature curve actually looks like per sample.

---

## Supported Benchmarks

| Dataset          | Category             | Size | Scoring     | Source                  |
| ---------------- | -------------------- | ---- | ----------- | ----------------------- |
| GSM8K            | Math reasoning       | 100  | exact_match | openai/gsm8k            |
| HumanEval        | Code generation      | 164  | code_exec   | openai/openai_humaneval |
| TruthfulQA       | Factual accuracy     | 100  | geval       | TruthfulQA/truthful_qa  |
| BBH              | Multi-step reasoning | 100  | exact_match | lukaemon/bbh            |
| Academic Writing | Technical writing    | 30   | geval       | Custom                  |
| Creative Writing | Creative tasks       | 30   | geval       | Custom                  |
| WMT Translate    | Translation (ro-en)  | 50   | geval       | wmt/wmt16               |

---

## Roadmap

### Phase 1 — Foundation ✅

- [x] Unified dataset registry and JSONL format
- [x] Temperature sweep framework
- [x] Multi-scoring pipeline (exact_match, code_exec, geval)
- [x] LiteLLM integration for model-agnostic inference
- [x] Arize Phoenix observability

### Phase 2 — Agent Evaluation 🔨

- [ ] Multi-turn agent conversation harness
- [ ] Tool-use evaluation (function calling accuracy, schema compliance)
- [ ] Agent trajectory scoring — not just final answer, but path quality
- [ ] ReAct / CoT / planning pattern comparison
- [ ] Agent benchmark datasets (SWE-bench subset, WebArena tasks)

### Phase 3 — Scale & Rigor

- [ ] Cartesian product runner — all models × all temperatures × all datasets in one command
- [ ] Statistical significance testing (bootstrap confidence intervals on GEval scores)
- [ ] Regression detection — alert when a model update degrades performance on any category
- [ ] Cost-normalized scoring (quality per dollar, quality per token)
- [ ] CI/CD integration — run evals on every PR, gate merges on quality thresholds

### Phase 4 — Extensibility

- [ ] Plugin system for custom metrics
- [ ] Dataset contribution guidelines and validation
- [ ] Web dashboard for experiment results
- [ ] Export to common formats (W&B, MLflow, CSV)
- [ ] Distributed execution (run sweeps across multiple GPU workers)

---

## Project Structure

```
llm-experiments/
├── models.json.example       # Model configuration template
├── pyproject.toml             # Dependencies (uv/pip)
├── datasets/
│   ├── registry.yaml          # Dataset catalog (machine-readable)
│   ├── scripts/
│   │   └── fetch_datasets.py  # Download & convert to JSONL
│   ├── math/                  # GSM8K
│   ├── coding/                # HumanEval
│   ├── factual/               # TruthfulQA
│   ├── reasoning/             # BBH
│   ├── writing/               # Academic writing
│   ├── creative_writing/      # Creative tasks
│   └── translation/           # WMT subset
├── experiments/
│   ├── conftest.py            # Pytest fixtures & CLI options
│   ├── config.py              # Shared configuration
│   ├── example.py             # Minimal working example
│   └── basic/                 # Temperature sweep experiments
└── .deepeval/                 # DeepEval cache & results
```

---

## Adding Your Own Dataset

1. Create a JSONL file in the appropriate `datasets/<category>/` directory
2. Follow the unified JSONL schema (see [Dataset Format](#dataset-format))
3. Register it in `datasets/registry.yaml`
4. Add scoring config in `experiments/config.py` → `DATASET_CONFIG`

```yaml
# registry.yaml
- name: my_dataset
  category: reasoning
  source: custom
  license: MIT
  split: test
  target_size: 50
  scoring: exact_match
  description: "Custom reasoning benchmark"
```

---

## Adding a Model

Just add an entry to `models.json`. LiteLLM handles the rest:

```json
{
  "my_model": {
    "model": "openai/my-finetune",
    "api_key": "sk-...",
    "api_base": "https://my-endpoint.example.com/v1"
  }
}
```

Works with: OpenAI, Anthropic, Google, AWS Bedrock, Azure, vLLM, Ollama, LM Studio, Together AI, Groq, any OpenAI-compatible API.

---

## Contributing

This is an early-stage project. Contributions welcome in:

- **New datasets** — follow the JSONL schema, include licensing info
- **New metrics** — extend the scoring pipeline for your domain
- **Agent eval** — the Phase 2 roadmap needs builders
- **Bug reports** — if something breaks, we want to know

---

## Tech Stack

| Component          | Technology             | Why                                    |
| ------------------ | ---------------------- | -------------------------------------- |
| Test runner        | pytest                 | Ecosystem, CI integration, parallelism |
| LLM interface      | LiteLLM                | 100+ providers, one API                |
| Metrics            | DeepEval               | GEval, caching, model abstraction      |
| Datasets           | HuggingFace `datasets` | Standard registry, streaming           |
| Tracing            | Arize Phoenix          | Open-source, OTel-compatible, local    |
| Package management | uv                     | Fast, reproducible lockfiles           |
| Config             | JSON + YAML            | Human-readable, git-friendly           |

---

## License

MIT
