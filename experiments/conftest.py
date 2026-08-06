"""
Top-level conftest for all experiments.

Provides CLI options for filtering experiments.
"""

import pytest


def pytest_addoption(parser):
    """Add experiment-specific CLI options."""
    parser.addoption(
        "--test-llm-model",
        type=str,
        default="default",
        help="Model name from models.json (default: 'default').",
    )
    parser.addoption(
        "--judge-llm-model",
        type=str,
        default="judge",
        help="Model name from models.json (default: 'judge').",
    )
