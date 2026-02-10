from __future__ import annotations

from pathlib import Path

import pytest

from sv_ref.core.analyzer import analyze
from sv_ref.core.models import Refbook

SAMPLES_DIR = Path(__file__).parent / "samples"


@pytest.fixture
def basic_types_refbook() -> Refbook:
    return analyze([SAMPLES_DIR / "basic_types.sv"])


@pytest.fixture
def nested_refbook() -> Refbook:
    return analyze([SAMPLES_DIR / "nested.sv"])


@pytest.fixture
def signed_refbook() -> Refbook:
    return analyze([SAMPLES_DIR / "signed_types.sv"])


@pytest.fixture
def wide_types_refbook() -> Refbook:
    return analyze([SAMPLES_DIR / "wide_types.sv"])


@pytest.fixture
def module_types_refbook() -> Refbook:
    return analyze([SAMPLES_DIR / "module_types.sv"])
