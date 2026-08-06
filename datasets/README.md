# Datasets

Unified test datasets for temperature experiments.

## Structure

```
datasets/
├── registry.yaml          # Machine-readable dataset catalog
├── scripts/
│   └── fetch_datasets.py  # Download & convert to unified JSONL
├── math/                  # GSM8K - grade school math
├── coding/                # HumanEval - Python code generation
├── factual/               # TruthfulQA - factual accuracy
├── reasoning/             # BBH - multi-step reasoning
├── writing/               # Academic writing (custom)
├── creative_writing/      # Creative writing (custom)
└── translation/           # Translation (custom subset)
```

## Unified JSONL Format

Every dataset is stored as JSONL with this schema:

```json
{
  "id": "unique_id",
  "category": "math|coding|factual|reasoning|writing|creative_writing|translation",
  "input": "the prompt / question",
  "expected_output": "ground truth answer (null for subjective tasks)",
  "metadata": {
    "difficulty": "easy|medium|hard",
    "source": "dataset_name",
    "scoring": "exact_match|code_exec|geval",
    "extra": {}
  }
}
```

For `code_exec` scoring, entries include a `test_cases` field:

```json
{
  "test_cases": ["assert solution(1) == True", "assert solution(2) == False"]
}
```

For `geval` scoring, entries include a `rubric` field:

```json
{
  "rubric": {
    "clarity": "Is the writing clear and well-structured?",
    "accuracy": "Is the content factually accurate?"
  }
}
```

## Scoring Methods

| Method        | Used By                                 | How                                       |
| ------------- | --------------------------------------- | ----------------------------------------- |
| `exact_match` | math, reasoning                         | Extract final answer, compare to expected |
| `code_exec`   | coding                                  | Run test cases against generated code     |
| `geval`       | factual, writing, creative, translation | LLM-as-judge with deepeval GEval          |

## Quick Start

```bash
# Install dependencies
uv sync

# Download all datasets (creates JSONL files in each category dir)
python datasets/scripts/fetch_datasets.py

# Download a specific dataset
python datasets/scripts/fetch_datasets.py --dataset gsm8k

# List available datasets
python datasets/scripts/fetch_datasets.py --list
```

## Adding Custom Datasets

1. Create JSONL file in the appropriate category directory
2. Follow the unified format above
3. Add entry to `registry.yaml` if it's a reusable dataset
