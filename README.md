# 🔬 LLM Eval Platform

> Production-grade LLM evaluation platform. Battery included.

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![uv](https://img.shields.io/badge/package%20manager-uv-black.svg)](https://github.com/astral-sh/uv)

---

## Why This Exists

LLM evaluation is broken. You have:

- Scattered scripts that run evals once and disappear
- No way to track whether your prompt v2 is actually better than v1
- No comparison framework — just manual "looks better to me"
- Metrics that don't match your actual use case
- Zero visibility into what's happening during evaluation

**LLM Eval Platform** fixes this. It's a complete, production-ready evaluation system with everything you need out of the box:

✅ **Datasets** — Download from HuggingFace or import your own, managed in-platform  
✅ **Metrics** — Built-in exact match, code execution, LLM-as-judge, and custom metrics  
✅ **Tracing** — Full observability for every inference and judgment  
✅ **History** — Track every evaluation run, compare across time  
✅ **Comparison** — A/B test prompts, models, temperatures, agent architectures

No more reinventing eval infrastructure. Just evaluate.

---

## Core Modules

### 📦 Datasets

Unified dataset management with zero friction.

**From HuggingFace:**

```bash
# Download and register datasets automatically
python datasets/scripts/fetch_datasets.py --dataset gsm8k
python datasets/scripts/fetch_datasets.py --all
```

**From your own files:**

```python
# Import custom datasets via CLI or API
python -m eval_platform.datasets import \
  --file my_data.jsonl \
  --category reasoning \
  --name "my-benchmark"
```

**In-platform management:**

- All datasets stored in unified JSONL format
- Registry tracks metadata (source, license, size, scoring method)
- Version-controlled, reproducible
- Browse, filter, and manage via CLI or future web UI

**Supported sources:**

- HuggingFace Datasets (auto-download + convert)
- Local JSONL/JSON/CSV files
- Custom formats via adapters

### 📊 Metrics

Battery-included evaluation metrics for every use case.

**Built-in metrics:**

| Metric                   | Use Case                                          | Implementation                         |
| ------------------------ | ------------------------------------------------- | -------------------------------------- |
| **Exact Match**          | Math, reasoning, factual QA                       | Regex extraction + string comparison   |
| **Code Execution**       | Code generation                                   | Sandboxed execution against test cases |
| **GEval (LLM-as-Judge)** | Subjective tasks (writing, translation, creative) | Calibrated LLM scoring with rubrics    |
| **BLEU/ROUGE**           | Translation, summarization                        | n-gram overlap metrics                 |
| **Semantic Similarity**  | Paraphrase, embedding quality                     | Cosine similarity on embeddings        |
| **Custom Metrics**       | Your domain                                       | Plugin system for arbitrary logic      |

**Example usage:**

```python
from eval_platform.metrics import GEval, ExactMatch, CodeExec

# LLM-as-judge with custom rubric
metric = GEval(
    name="Clarity",
    criteria="Is the explanation clear and well-structured?",
    threshold=0.7,
    model="gpt-4o"
)

# Exact match for deterministic tasks
metric = ExactMatch(extract_pattern=r"The answer is: (\d+)")

# Code execution with sandbox
metric = CodeExec(timeout=5, test_cases=[...])
```

**Extending metrics:**

```python
# Custom metric plugin
class MyMetric(BaseMetric):
    def score(self, input: str, output: str, expected: str) -> float:
        # Your logic here
        return 0.95
```

### 🔍 Tracing

Full observability into every evaluation run.

**What's traced:**

- Every LLM inference (prompt, completion, latency, tokens)
- Every metric computation (judge reasoning, scores)
- Dataset loading and preprocessing
- Errors and exceptions

**Powered by Arize Phoenix:**

```bash
# Start tracing UI
python -m phoenix.server.main serve
# Open http://localhost:6006
```

**What you get:**

- Trace waterfall (parent → child spans)
- Token usage and cost tracking
- Latency breakdown
- Error inspection
- Filter by model, dataset, metric, time range

**Why this matters:**
When your eval says "Model A beats Model B," tracing shows you _why_. Inspect specific examples, see where the judge disagreed, identify latency bottlenecks.

### 📈 History & Reports

Track every evaluation run. Compare across time.

**Automatic tracking:**

```bash
# Every run is logged
pytest experiments/ -v
# Results saved to .eval_platform/runs/
```

**What's stored:**

- Run metadata (timestamp, config, git commit)
- Per-sample results (input, output, expected, score)
- Aggregate metrics (mean, median, std, confidence intervals)
- Model configs, prompt templates, hyperparameters

**Query history:**

```bash
# List all runs
eval-platform history list

# Show details for a specific run
eval-platform history show run_2024_01_15_14_30

# Compare two runs
eval-platform history compare run_123 run_456
```

**Use cases:**

- Track quality improvements after prompt engineering
- Detect regressions after model updates
- Audit evaluation results for compliance
- Build dashboards for team visibility

### ⚖️ Comparison

Systematic A/B testing for LLM experiments.

**Compare anything:**

```bash
# Same task, different prompts
eval-platform compare \
  --run-baseline prompt_v1 \
  --run-experiment prompt_v2 \
  --dataset gsm8k

# Same prompt, different models
eval-platform compare \
  --run-baseline gpt-4o \
  --run-experiment claude-3.5-sonnet \
  --dataset reasoning

# Same model, different temperatures
eval-platform compare \
  --run-baseline temp_0.0 \
  --run-experiment temp_0.7 \
  --dataset creative_writing
```

**What you get:**

- Side-by-side score comparison
- Statistical significance testing (bootstrap CI)
- Per-sample breakdown (which examples improved/regressed)
- Visualization (charts, heatmaps)

**Advanced comparisons:**

- Cartesian product: all models × all prompts × all datasets
- Regression detection: alert on quality degradation
- Cost-normalized comparison: quality per dollar

---

## Quick Start

### Installation

```bash
git clone https://github.com/<your-org>/llm-eval-platform.git
cd llm-eval-platform

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### Configuration

**1. Configure models:**

```bash
cp models.json.example models.json
```

```jsonc
// models.json
{
  "gpt-4o": {
    "model": "openai/gpt-4o",
    "api_key": "sk-...",
    "api_base": "https://api.openai.com/v1",
  },
  "claude": {
    "model": "anthropic/claude-3-5-sonnet-20241022",
    "api_key": "sk-ant-...",
  },
  "local": {
    "model": "openai/llama-3.1-8b",
    "api_key": "no_key",
    "api_base": "http://localhost:11434/v1",
  },
  "judge": {
    "model": "openai/gpt-4o",
    "api_key": "sk-...",
  },
}
```

**2. Fetch datasets:**

```bash
# Download all benchmark datasets
python datasets/scripts/fetch_datasets.py --all

# Or specific datasets
python datasets/scripts/fetch_datasets.py --dataset gsm8k,humaneval
```

**3. Start tracing:**

```bash
python -m phoenix.server.main serve
```

**4. Run your first evaluation:**

```bash
# Basic correctness test
pytest experiments/example.py -v

# Temperature sweep
pytest experiments/basic/temperature/ -v

# With specific model
pytest experiments/ -v --test-llm-model gpt-4o
```

**5. View results:**

```bash
# List evaluation history
eval-platform history list

# Compare runs
eval-platform compare run_001 run_002

# Open tracing UI
open http://localhost:6006
```

---

## Usage Examples

### Example 1: Prompt Engineering A/B Test

You've rewritten your system prompt. Is it actually better?

```bash
# Run baseline (old prompt)
pytest experiments/ -v \
  --prompt-template prompts/v1.txt \
  --dataset gsm8k \
  --run-name "prompt_v1"

# Run experiment (new prompt)
pytest experiments/ -v \
  --prompt-template prompts/v2.txt \
  --dataset gsm8k \
  --run-name "prompt_v2"

# Compare
eval-platform compare prompt_v1 prompt_v2
```

**Output:**

```
Comparison: prompt_v1 vs prompt_v2
Dataset: gsm8k (100 samples)

Metric: Exact Match
  prompt_v1: 72.0% ± 4.5%
  prompt_v2: 78.0% ± 4.1%
  Delta: +6.0% (p < 0.05) ✓

Per-sample breakdown:
  Improved: 12 samples
  Regressed: 6 samples
  Unchanged: 82 samples
```

### Example 2: Model Selection

Which model performs best on your task?

```bash
# Evaluate multiple models
for model in gpt-4o claude local-llama; do
  pytest experiments/ -v \
    --test-llm-model $model \
    --dataset my_task \
    --run-name "model_$model"
done

# Compare all
eval-platform compare model_gpt-4o model_claude model_local-llama
```

### Example 3: Temperature Optimization

Find the optimal temperature for your use case.

```bash
# Run temperature sweep (0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0)
pytest experiments/basic/temperature/ -v \
  --test-llm-model gpt-4o \
  --dataset creative_writing

# Analyze results
eval-platform history show temp_sweep_001
```

### Example 4: Custom Dataset

Evaluate on your proprietary data.

```bash
# 1. Prepare your dataset (JSONL format)
cat > my_eval.jsonl << 'EOF'
{"id": "1", "input": "What is our refund policy?", "expected_output": "30 days..."}
{"id": "2", "input": "How do I upgrade?", "expected_output": "Go to settings..."}
EOF

# 2. Import to platform
eval-platform datasets import \
  --file my_eval.jsonl \
  --category qa \
  --name "internal-qa-bench"

# 3. Run evaluation
pytest experiments/ -v --dataset internal-qa-bench
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI / Web UI                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Datasets │  │ Metrics  │  │ Tracing  │  │  History   │  │
│  │          │  │          │  │          │  │  & Report  │  │
│  │ HF Hub   │  │ Exact    │  │ Phoenix  │  │            │  │
│  │ Custom   │  │ CodeExec │  │ OpenTel  │  │ Run logs   │  │
│  │ Registry │  │ GEval    │  │ Spans    │  │ Compare    │  │
│  │ JSONL    │  │ Custom   │  │ Latency  │  │ Regression │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                   Experiment Runner                          │
│            (pytest + LiteLLM + DeepEval)                     │
├─────────────────────────────────────────────────────────────┤
│                   Storage Layer                              │
│         (JSONL datasets, SQLite history, traces)             │
└─────────────────────────────────────────────────────────────┘
```

**Design principles:**

- **Battery included** — everything works out of the box
- **Extensible** — plugin system for custom metrics, datasets, exporters
- **Observable** — full tracing, no black boxes
- **Reproducible** — declarative configs, versioned datasets, deterministic execution
- **Production-ready** — error handling, retries, cost tracking, CI/CD integration

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

**Adding your own:** See [Datasets module](#-datasets)

---

## Roadmap

### Phase 1 — Core Platform ✅

- [x] Unified dataset management (HF + custom import)
- [x] Built-in metrics (exact match, code exec, GEval)
- [x] Tracing integration (Arize Phoenix)
- [x] Evaluation history tracking
- [x] Basic comparison framework

### Phase 2 — Agent Evaluation 🔨

- [ ] Multi-turn agent conversation harness
- [ ] Tool-use evaluation (function calling accuracy, schema compliance)
- [ ] Agent trajectory scoring (path quality, not just final answer)
- [ ] ReAct / CoT / planning pattern comparison
- [ ] Agent benchmark datasets (SWE-bench, WebArena)

### Phase 3 — Advanced Features

- [ ] Statistical significance testing (bootstrap CI)
- [ ] Regression detection (alert on quality degradation)
- [ ] Cost-normalized scoring (quality per dollar, quality per token)
- [ ] CI/CD integration (GitHub Actions, GitLab CI templates)
- [ ] Distributed execution (run sweeps across multiple workers)

### Phase 4 — Web Platform

- [ ] Web UI for dataset management
- [ ] Interactive comparison dashboard
- [ ] Team collaboration (shared runs, comments, annotations)
- [ ] API for programmatic access
- [ ] Export to W&B, MLflow, CSV, JSON

### Phase 5 — Extensibility

- [ ] Plugin marketplace (community metrics, datasets)
- [ ] Custom metric SDK
- [ ] Dataset contribution guidelines
- [ ] Self-hosted deployment guide
- [ ] Enterprise features (SSO, RBAC, audit logs)

---

## Project Structure

```
llm-eval-platform/
├── models.json.example          # Model configuration
├── pyproject.toml               # Dependencies
├── datasets/
│   ├── registry.yaml            # Dataset catalog
│   ├── scripts/
│   │   └── fetch_datasets.py    # HF download + conversion
│   ├── math/                    # GSM8K
│   ├── coding/                  # HumanEval
│   ├── factual/                 # TruthfulQA
│   ├── reasoning/               # BBH
│   ├── writing/                 # Academic
│   ├── creative_writing/        # Creative
│   └── translation/             # WMT
├── experiments/
│   ├── conftest.py              # Pytest fixtures
│   ├── config.py                # Shared config
│   ├── example.py               # Minimal example
│   └── basic/
│       └── temperature/         # Temperature sweep
└── .eval_platform/              # Run history (auto-generated)
```

---

## Tech Stack

| Component           | Technology             | Why                                    |
| ------------------- | ---------------------- | -------------------------------------- |
| **Test runner**     | pytest                 | Ecosystem, CI integration, parallelism |
| **LLM interface**   | LiteLLM                | 100+ providers, one API                |
| **Metrics**         | DeepEval               | GEval, caching, model abstraction      |
| **Datasets**        | HuggingFace `datasets` | Standard registry, streaming           |
| **Tracing**         | Arize Phoenix          | Open-source, OTel-compatible, local    |
| **History**         | SQLite + JSONL         | Simple, portable, queryable            |
| **Package manager** | uv                     | Fast, reproducible lockfiles           |

---

## Contributing

This is an early-stage project. We're building the evaluation platform we wish existed.

**Ways to contribute:**

- **Datasets** — add benchmarks for your domain
- **Metrics** — implement new evaluation methods
- **Agent eval** — help build Phase 2
- **Web UI** — design the dashboard
- **Bug reports** — if something breaks, we want to know

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## Comparison with Alternatives

| Feature                  | LLM Eval Platform | DeepEval | LangSmith | Custom Scripts |
| ------------------------ | ----------------- | -------- | --------- | -------------- |
| **Battery included**     | ✅                | ✅       | ❌        | ❌             |
| **Open source**          | ✅                | ✅       | ❌        | ✅             |
| **Dataset management**   | ✅                | ❌       | ❌        | ❌             |
| **Built-in tracing**     | ✅                | ❌       | ✅        | ❌             |
| **History tracking**     | ✅                | ❌       | ✅        | ❌             |
| **Comparison framework** | ✅                | ❌       | ⚠️        | ❌             |
| **Self-hosted**          | ✅                | ✅       | ❌        | ✅             |
| **Agent evaluation**     | 🔜                | ⚠️       | ✅        | ❌             |

---

## License

MIT

---

## Star History

If this project helps your LLM evaluation workflow, consider giving it a ⭐

---

**Built with ❤️ for the LLM community**

_Stop guessing. Start measuring._
