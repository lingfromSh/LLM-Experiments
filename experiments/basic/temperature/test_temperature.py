"""
Temperature experiment — test cases.

Tests how different temperature settings affect LLM performance across task types.
Each dataset type uses its own scoring strategy:

  exact_match  → extract answer, compare to ground truth   (math, reasoning)
  code_exec    → extract code, run test_cases              (coding)
  geval        → LLM-as-judge with rubric criteria         (factual, writing, …)

Usage:
    deepeval test run experiments/basic/temperature/test_temperature.py
"""

import litellm
import pytest
from itertools import product
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, SingleTurnParams
from phoenix.otel import register

from experiments.config import DATASET_CONFIG, get_model
from experiments.basic.temperature.conftest import load_dataset_entries
from experiments.basic.temperature.metrics import (
    score_exact_match,
    score_code_exec,
    build_geval_metric,
)

trace_provider = register(
    project_name="llm-experiments",
    auto_instrument=True,
    set_global_tracer_provider=False,
)


TEMPERATURES = [0.1, 0.3, 0.5, 0.7, 1]

tracer = trace_provider.get_tracer("temperature-experiments")


# ── LLM Call ────────────────────────────────────────────────────────────────


@tracer.chain
def call_llm(prompt: str, temperature: float) -> str:
    """Call the LLM via LiteLLM with given temperature."""
    cfg = get_model()
    response = litellm.completion(
        model=cfg["model"],
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=1024,
        api_key=cfg["api_key"],
        api_base=cfg["api_base"],
    )
    return response.choices[0].message.content


# ── Scoring Dispatchers ─────────────────────────────────────────────────────


def _get_scoring_method(dataset_category: str) -> str:
    """Determine scoring method from the first entry of a dataset."""
    entries = load_dataset_entries(dataset_category)
    if entries:
        return entries[0].get("metadata", {}).get("scoring", "geval")
    return "geval"


@tracer.chain
def _score_exact_match_entry(entry: dict, actual_output: str) -> dict:
    """Score a single exact_match entry."""
    result = score_exact_match(actual_output, entry["expected_output"])
    return result


@tracer.chain
def _score_code_exec_entry(entry: dict, actual_output: str) -> dict:
    """Score a single code_exec entry."""
    test_cases = entry.get("test_cases", [])
    result = score_code_exec(actual_output, test_cases)
    return result


@tracer.chain
def _score_geval_entry(entry: dict, actual_output: str, dataset_category: str, judge_model) -> dict:
    """Score a single geval entry using LLM-as-judge."""
    cfg = DATASET_CONFIG[dataset_category]
    metric = build_geval_metric(
        category=dataset_category,
        criteria=cfg["geval_criteria"],
        judge_model=judge_model,
    )
    test_case = LLMTestCase(
        input=entry["input"],
        actual_output=actual_output,
        expected_output=entry.get("expected_output"),
    )
    metric.measure(test_case)
    return {
        "score": metric.score,
        "reason": getattr(metric, "reason", None),
    }


# ── Tests ───────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    argnames="temperature,dataset_category",
    argvalues=list(product(TEMPERATURES, DATASET_CONFIG.keys())),
)
@tracer.chain
def test_temperature(temperature: float, dataset_category: str, judge_llm_model):
    """Test one (temperature, dataset) combination.

    Loads all samples for the dataset, generates responses at the given
    temperature, and evaluates using the scoring method appropriate for
    the dataset type:

      - exact_match (math, reasoning): extract answer, compare to ground truth
      - code_exec   (coding):          run test_cases against generated code
      - geval       (factual, writing, translation, …): LLM-as-judge
    """
    entries = load_dataset_entries(dataset_category)
    scoring = _get_scoring_method(dataset_category)

    for entry in entries:
        actual_output = call_llm(entry["input"], temperature)

        if scoring == "exact_match":
            _test_exact_match(entry, actual_output, temperature, dataset_category)
        elif scoring == "code_exec":
            _test_code_exec(entry, actual_output, temperature, dataset_category)
        elif scoring == "geval":
            _test_geval(entry, actual_output, temperature, dataset_category, judge_llm_model)
        else:
            pytest.fail(f"Unknown scoring method '{scoring}' for {dataset_category}")


def _test_exact_match(entry: dict, actual_output: str, temperature: float, category: str):
    """Assert that the extracted answer matches the expected output."""
    result = _score_exact_match_entry(entry, actual_output)

    assert result["match"], (
        f"[{category}, t={temperature}] Answer mismatch for {entry['id']}:\n"
        f"  Expected:  {result['expected']}\n"
        f"  Extracted: {result['extracted_answer']}\n"
        f"  Raw output (last 200 chars): …{actual_output[-200:]}"
    )


def _test_code_exec(entry: dict, actual_output: str, temperature: float, category: str):
    """Assert that generated code passes all test cases."""
    result = _score_code_exec_entry(entry, actual_output)

    assert result["score"] == 1.0, (
        f"[{category}, t={temperature}] Code test failures for {entry['id']}:\n"
        f"  Passed: {result['passed']}/{result['total']}\n"
        f"  Errors:\n" + "\n".join(f"    - {e}" for e in result["errors"][:5])
    )


def _test_geval(entry: dict, actual_output: str, temperature: float, category: str, judge_model):
    """Assert GEval score meets threshold using deepeval."""
    cfg = DATASET_CONFIG[category]
    metric = build_geval_metric(
        category=category,
        criteria=cfg["geval_criteria"],
        judge_model=judge_model,
    )

    assert_test(
        LLMTestCase(
            input=entry["input"],
            actual_output=actual_output,
            expected_output=entry.get("expected_output"),
        ),
        metrics=[metric],
    )
