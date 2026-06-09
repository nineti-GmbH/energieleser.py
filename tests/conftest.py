"""Shared fixtures for the energieleser test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> dict[str, Any]:
    val: dict[str, Any] = json.loads((FIXTURES_DIR / f"{name}.json").read_text(encoding="utf-8"))
    return val


@pytest.fixture
def stromleser_payload() -> dict[str, Any]:
    """Return the stromleser sample API response."""
    return _load_fixture("stromleser")


@pytest.fixture
def stromleser_single_phase_payload() -> dict[str, Any]:
    """Return a real single-phase stromleser response (no per-phase power)."""
    return _load_fixture("stromleser_single_phase")


@pytest.fixture
def gasleser_payload() -> dict[str, Any]:
    """Return the gasleser sample API response."""
    return _load_fixture("gasleser")


@pytest.fixture
def wasserleser_payload() -> dict[str, Any]:
    """Return the wasserleser sample API response."""
    return _load_fixture("wasserleser")


@pytest.fixture
def waermeleser_payload() -> dict[str, Any]:
    """Return the wärmeleser sample API response."""
    return _load_fixture("waermeleser")
