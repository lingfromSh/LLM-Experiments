"""
Shared experiment configuration.

Reads model definitions from experiments/models.json and provides
common paths and settings for all experiments.
"""

import json
from functools import lru_cache
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = Path(__file__).resolve().parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
MODELS_FILE = PROJECT_ROOT / "models.json"


# ── Models ─────────────────────────────────────────────────────────────────


@lru_cache
def load_models() -> dict:
    """Load model definitions from models.json."""
    with open(MODELS_FILE) as f:
        return json.load(f)


@lru_cache
def get_model(name: str = "default") -> dict:
    """Get a model config by name. Falls back to first model if name not found."""
    models = load_models()
    if name in models:
        return models[name]
    # Return default model
    if "default" in models:
        return models["default"]
    # Return first available model
    return next(iter(models.values()))


# ── Temperature Sweep ──────────────────────────────────────────────────────

TEMPERATURES = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]


# ── Dataset → Metric Mapping ──────────────────────────────────────────────

DATASET_CONFIG = {
    "math": {
        "file": "math/gsm8k_sample.jsonl",
        "description": "Math reasoning (GSM8K)",
        "hypothesis": "Low temperature (0.0-0.2) should perform best — math has deterministic answers",
        "geval_criteria": "Determine if the actual output contains the correct numerical answer compared to the expected output. The answer may be embedded in explanatory text.",
    },
    "coding": {
        "file": "coding/humaneval_sample.jsonl",
        "description": "Code generation (HumanEval)",
        "hypothesis": "Low temperature (0.0-0.3) should perform best — code must be syntactically correct",
        "geval_criteria": "Determine if the generated code is syntactically correct and logically implements the required functionality described in the input.",
    },
    "factual": {
        "file": "factual/truthfulqa_sample.jsonl",
        "description": "Factual accuracy (TruthfulQA)",
        "hypothesis": "Low temperature (0.0-0.2) should reduce hallucination",
        "geval_criteria": "Determine if the actual output is factually accurate and avoids common misconceptions or hallucinations, using the expected output as reference.",
    },
    "reasoning": {
        "file": "reasoning/bbh_sample.jsonl",
        "description": "Multi-step reasoning (BBH)",
        "hypothesis": "Low temperature (0.0-0.3) should perform best — logical deduction is deterministic",
        "geval_criteria": "Determine if the actual output contains the correct answer to the reasoning problem, comparing against the expected output.",
    },
    "writing": {
        "file": "writing/academic_sample.jsonl",
        "description": "Academic writing",
        "hypothesis": "Low-medium temperature (0.1-0.4) should balance precision and naturalness",
        "geval_criteria": "Evaluate the clarity, structure, academic tone, and completeness of the writing. Higher scores for well-organized, precise, and comprehensive responses.",
    },
    "creative_writing": {
        "file": "creative_writing/creative_sample.jsonl",
        "description": "Creative writing",
        "hypothesis": "Higher temperature (0.5-1.0) may produce more creative/diverse outputs",
        "geval_criteria": "Evaluate creativity, originality, coherence, and stylistic quality. Higher scores for imaginative, well-crafted, and engaging content.",
    },
    "translation": {
        "file": "translation/translation_sample.jsonl",
        "description": "Translation fidelity",
        "hypothesis": "Low temperature (0.0-0.2) should produce more faithful translations",
        "geval_criteria": "Evaluate translation accuracy, fluency, and faithfulness to the source text. Compare against the reference translation.",
    },
}
