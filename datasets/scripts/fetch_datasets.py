"""
Fetch datasets from HuggingFace and convert to unified JSONL format.

Usage:
    python datasets/scripts/fetch_datasets.py              # Fetch all
    python datasets/scripts/fetch_datasets.py --dataset gsm8k
    python datasets/scripts/fetch_datasets.py --list
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

DATASETS_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = DATASETS_DIR / "registry.yaml"

# Category -> directory mapping
CATEGORY_DIRS = {
    "math": "math",
    "coding": "coding",
    "factual": "factual",
    "reasoning": "reasoning",
    "writing": "writing",
    "creative_writing": "creative_writing",
    "translation": "translation",
}


def load_registry() -> list[dict]:
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)["datasets"]


def write_jsonl(path: Path, entries: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  ✓ Wrote {len(entries)} entries to {path}")


# ── GSM8K ──────────────────────────────────────────────────────────────────

def fetch_gsm8k(target_size: int) -> list[dict]:
    """Fetch GSM8K math problems. Extract final numeric answer from #### format."""
    from datasets import load_dataset

    ds = load_dataset("openai/gsm8k", "main", split="test")
    entries = []
    for i, item in enumerate(ds):
        if i >= target_size:
            break
        # Extract the final answer after ####
        answer_text = item["answer"]
        match = re.search(r"####\s*(.+)", answer_text)
        final_answer = match.group(1).strip() if match else answer_text

        entries.append({
            "id": f"gsm8k_{i:04d}",
            "category": "math",
            "input": item["question"],
            "expected_output": final_answer,
            "metadata": {
                "difficulty": "medium",
                "source": "gsm8k",
                "scoring": "exact_match",
            },
        })
    return entries


# ── HumanEval ──────────────────────────────────────────────────────────────

def fetch_humaneval(target_size: int) -> list[dict]:
    """Fetch HumanEval coding problems with test cases."""
    from datasets import load_dataset

    ds = load_dataset("openai/openai_humaneval", split="test")
    entries = []
    for i, item in enumerate(ds):
        if i >= target_size:
            break

        # Parse test cases from the "test" field
        test_str = item.get("test", "")
        # Extract assert lines
        test_cases = [
            line.strip()
            for line in test_str.split("\n")
            if line.strip().startswith("assert ") or line.strip().startswith("assert(")
        ]
        # Add the check line
        if "check(" in test_str:
            for line in test_str.split("\n"):
                if "check(" in line and line.strip().startswith("check"):
                    test_cases.append(line.strip())

        entries.append({
            "id": f"humaneval_{i:03d}",
            "category": "coding",
            "input": item["prompt"],
            "expected_output": None,
            "test_cases": test_cases,
            "metadata": {
                "difficulty": "medium",
                "source": "humaneval",
                "scoring": "code_exec",
                "entry_point": item.get("entry_point", f"candidate_{i}"),
            },
        })
    return entries


# ── TruthfulQA ─────────────────────────────────────────────────────────────

def fetch_truthfulqa(target_size: int) -> list[dict]:
    """Fetch TruthfulQA generation split."""
    from datasets import load_dataset

    ds = load_dataset("truthyqa/truthful_qa", "generation", split="validation")
    entries = []
    for i, item in enumerate(ds):
        if i >= target_size:
            break

        # Best answer as expected output
        best_answer = item.get("best_answer", item.get("correct_answers", [""])[0])
        correct_answers = item.get("correct_answers", [])
        incorrect_answers = item.get("incorrect_answers", [])

        # Build a rubric for GEval
        rubric = {
            "truthfulness": "Does the response avoid common misconceptions and provide factually accurate information?",
            "completeness": "Does the response adequately address the question?",
        }

        entries.append({
            "id": f"truthfulqa_{i:04d}",
            "category": "factual",
            "input": item["question"],
            "expected_output": best_answer,
            "metadata": {
                "difficulty": "medium",
                "source": "truthfulqa",
                "scoring": "geval",
                "rubric": rubric,
                "correct_answers": correct_answers[:3],
                "incorrect_answers": incorrect_answers[:3],
            },
        })
    return entries


# ── BBH (BIG-Bench Hard) ──────────────────────────────────────────────────

def fetch_bbh(target_size: int) -> list[dict]:
    """Fetch BBH reasoning tasks from lukaemon/bbh."""
    from datasets import load_dataset

    # Load multiple BBH subtasks
    subtasks = [
        "sports_understanding",
        "causal_judgement",
        "multi_step_arithmetic",
        "logical_deduction",
        "boolean_expressions",
    ]

    entries = []
    global_idx = 0

    for subtask in subtasks:
        try:
            ds = load_dataset("lukaemon/bbh", subtask, split="test")
        except Exception as e:
            print(f"  ⚠ Could not load BBH subtask '{subtask}': {e}")
            continue

        per_task_limit = max(1, target_size // len(subtasks))
        for i, item in enumerate(ds):
            if i >= per_task_limit:
                break
            if global_idx >= target_size:
                break

            entries.append({
                "id": f"bbh_{subtask}_{i:03d}",
                "category": "reasoning",
                "input": item.get("input", item.get("question", "")),
                "expected_output": item.get("target", item.get("answer", "")),
                "metadata": {
                    "difficulty": "hard",
                    "source": "bbh",
                    "scoring": "exact_match",
                    "task": subtask,
                },
            })
            global_idx += 1

        if global_idx >= target_size:
            break

    return entries


# ── Translation (WMT) ─────────────────────────────────────────────────────

def fetch_wmt(target_size: int) -> list[dict]:
    """Fetch a small WMT translation subset."""
    from datasets import load_dataset

    try:
        ds = load_dataset("wmt16", "ro-en", split="test")
    except Exception as e:
        print(f"  ⚠ Could not load WMT: {e}")
        print("  → Using sample data instead. See datasets/translation/translation_sample.jsonl")
        return []

    entries = []
    for i, item in enumerate(ds):
        if i >= target_size:
            break
        en_text = item["translation"]["en"]
        ro_text = item["translation"]["ro"]

        entries.append({
            "id": f"wmt_{i:04d}",
            "category": "translation",
            "input": f"Translate the following from English to Romanian:\n\n\"{en_text}\"",
            "expected_output": ro_text,
            "metadata": {
                "difficulty": "medium",
                "source": "wmt16",
                "scoring": "geval",
                "rubric": {
                    "accuracy": "Is the translation accurate and complete?",
                    "fluency": "Does the target language read naturally?",
                },
            },
        })
    return entries


# ── Dispatcher ─────────────────────────────────────────────────────────────

FETCHERS = {
    "gsm8k": ("math/gsm8k.jsonl", fetch_gsm8k),
    "humaneval": ("coding/humaneval.jsonl", fetch_humaneval),
    "truthfulqa": ("factual/truthfulqa.jsonl", fetch_truthfulqa),
    "bbh": ("reasoning/bbh.jsonl", fetch_bbh),
    "wmt_translate": ("translation/wmt.jsonl", fetch_wmt),
}


def main():
    parser = argparse.ArgumentParser(description="Fetch datasets for temperature experiments")
    parser.add_argument("--dataset", type=str, help="Fetch a specific dataset by name")
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    registry = load_registry()

    if args.list:
        print("Available datasets:")
        for ds in registry:
            status = "✓ fetched" if ds["source"] == "custom" else "pending"
            print(f"  {ds['name']:20s} [{ds['category']:18s}] {ds['source']:30s} → {status}")
        return

    to_fetch = registry
    if args.dataset:
        to_fetch = [d for d in registry if d["name"] == args.dataset]
        if not to_fetch:
            print(f"Dataset '{args.dataset}' not found in registry.")
            sys.exit(1)

    for ds_info in to_fetch:
        name = ds_info["name"]
        if name not in FETCHERS:
            print(f"\n⊘ Skipping '{name}' (custom dataset — use sample JSONL)")
            continue

        rel_path, fetcher = FETCHERS[name]
        out_path = DATASETS_DIR / rel_path

        if out_path.exists() and not args.force:
            print(f"\n⊘ Skipping '{name}' — {out_path} exists (use --force to overwrite)")
            continue

        print(f"\n→ Fetching {name} from {ds_info['source']}...")
        try:
            entries = fetcher(ds_info["target_size"])
            if entries:
                write_jsonl(out_path, entries)
        except Exception as e:
            print(f"  ✗ Failed to fetch {name}: {e}")
            print(f"    You can use the sample data at datasets/{rel_path.replace('.jsonl', '_sample.jsonl')}")

    print("\nDone. Dataset files are ready for temperature experiments.")


if __name__ == "__main__":
    main()
