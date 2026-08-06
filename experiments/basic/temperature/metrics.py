"""
Temperature experiment — scoring metrics.

Three evaluation strategies, dispatched by dataset metadata:

  exact_match  — extract the final answer, compare to ground truth (math, reasoning)
  code_exec    — extract code, run test_cases, report pass rate (coding)
  geval        — LLM-as-judge with rubric criteria (factual, writing, translation, …)
"""

import re

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, SingleTurnParams


# ── 1. Exact Match ──────────────────────────────────────────────────────────

_ANSWER_PATTERNS = [
    # "The answer is 42" / "The answer is: 42"
    re.compile(r"[Tt]he\s+(?:final\s+)?answer\s+is[:\s]+(.+?)(?:\.|$|\n)"),
    # "= 42" at end of line
    re.compile(r"=\s*(.+?)$", re.MULTILINE),
    # "#### 42"  (GSM8K convention)
    re.compile(r"####\s*(.+?)(?:\n|$)"),
]


def _extract_answer(text: str) -> str:
    """Try multiple heuristics to pull the final answer out of LLM output."""
    for pattern in _ANSWER_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(1).strip().rstrip(".")
    # Fallback: last number-like token on the last non-empty line
    for line in reversed(text.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        # grab the last number (int or float) on this line
        nums = re.findall(r"-?\d+(?:\.\d+)?", line)
        if nums:
            return nums[-1]
    return text.strip()


def _normalize(text: str) -> str:
    """Normalize for comparison: lowercase, strip whitespace/punctuation."""
    return re.sub(r"[^\w]", "", text.lower())


def score_exact_match(actual_output: str, expected_output: str) -> dict:
    """Score by extracting the answer and comparing to ground truth.

    Returns dict with: score (0|1), extracted_answer, expected, match.
    """
    extracted = _extract_answer(actual_output)
    expected = expected_output.strip()
    match = _normalize(extracted) == _normalize(expected)
    return {
        "score": 1.0 if match else 0.0,
        "extracted_answer": extracted,
        "expected": expected,
        "match": match,
    }


# ── 2. Code Execution ───────────────────────────────────────────────────────

_CODE_BLOCK_RE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str | None:
    """Extract the first Python code block from LLM output."""
    m = _CODE_BLOCK_RE.search(text)
    if m:
        return m.group(1).strip()
    return None


def score_code_exec(actual_output: str, test_cases: list[str]) -> dict:
    """Score by executing test cases against the generated code.

    Returns dict with: score (pass_rate), passed, total, errors, code.
    """
    code = _extract_code(actual_output)
    if code is None:
        return {
            "score": 0.0,
            "passed": 0,
            "total": len(test_cases),
            "errors": ["No code block found in output"],
            "code": None,
        }

    passed = 0
    errors = []
    for tc in test_cases:
        try:
            exec(code + "\n" + tc, {})
            passed += 1
        except Exception as e:
            errors.append(f"{tc} → {type(e).__name__}: {e}")

    total = len(test_cases)
    return {
        "score": passed / total if total > 0 else 0.0,
        "passed": passed,
        "total": total,
        "errors": errors,
        "code": code,
    }


# ── 3. GEval (LLM-as-Judge) ────────────────────────────────────────────────

def build_geval_metric(
    category: str,
    criteria: str,
    judge_model,
    threshold: float = 0.5,
) -> GEval:
    """Build a GEval metric with category-specific evaluation criteria."""
    return GEval(
        name=category,
        criteria=criteria,
        evaluation_params=[
            SingleTurnParams.INPUT,
            SingleTurnParams.ACTUAL_OUTPUT,
            SingleTurnParams.EXPECTED_OUTPUT,
        ],
        threshold=threshold,
        model=judge_model,
    )


# ── Dispatcher ──────────────────────────────────────────────────────────────

def score_entry(dataset_category: str, entry: dict, actual_output: str, judge_model=None):
    """Route to the correct scorer based on dataset category.

    Args:
        dataset_category: one of the keys in DATASET_CONFIG
        entry: the original dataset entry dict (with metadata, test_cases, etc.)
        actual_output: the LLM response text
        judge_model: a deepeval LiteLLMModel instance (required for geval)

    Returns:
        dict with at least a "score" key (0.0–1.0) plus scorer-specific details.
    """
    scoring = entry.get("metadata", {}).get("scoring", "geval")

    if scoring == "exact_match":
        return score_exact_match(actual_output, entry["expected_output"])

    elif scoring == "code_exec":
        test_cases = entry.get("test_cases", [])
        return score_code_exec(actual_output, test_cases)

    elif scoring == "geval":
        if judge_model is None:
            raise ValueError("judge_model is required for geval scoring")
        from experiments.config import DATASET_CONFIG
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
            "geval_name": metric.name,
        }

    else:
        raise ValueError(f"Unknown scoring method: {scoring}")
