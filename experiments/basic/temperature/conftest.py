"""
Temperature experiment — conftest.

Provides llm_model fixture and parametrization matrix.
"""

import json
from pathlib import Path

import pytest
from deepeval.models import LiteLLMModel
from experiments.config import DATASET_CONFIG, DATASETS_DIR, get_model

# ── Dataset Loading ────────────────────────────────────────────────────────


def load_dataset_entries(category: str) -> list[dict]:
    """Load all samples for a dataset category."""
    config = DATASET_CONFIG[category]
    path = DATASETS_DIR / config["file"]
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def test_llm_model(request) -> LiteLLMModel:
    """Session-scoped LLM model for generating responses."""
    model_name = request.config.getoption("--test-llm-model")
    cfg = get_model(model_name)
    return LiteLLMModel(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["api_base"],
    )


@pytest.fixture(scope="session")
def judge_llm_model(request) -> LiteLLMModel:
    """Session-scoped LLM model for generating responses."""
    model_name = request.config.getoption("--judge-llm-model")
    cfg = get_model(model_name)
    return LiteLLMModel(
        model=cfg["model"],
        api_key=cfg["api_key"],
        base_url=cfg["api_base"],
    )
