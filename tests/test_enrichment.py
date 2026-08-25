"""
Tests for enrichment module — verifies re-exports work correctly.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from enrichment import (
    interpret_abg,
    calculate_anion_gap,
    winters_formula,
    assess_winters,
    calculate_delta_ratio,
    interpret_row,
    process_csv,
)


def test_enrichment_re_exports_interpret_abg():
    """Verify enrichment module re-exports interpret_abg correctly."""
    result = interpret_abg(7.40, 40.0, 24.0)
    assert result["primary_disorder"] == "normal"


def test_enrichment_re_exports_anion_gap():
    """Verify enrichment module re-exports anion gap calculation."""
    result = calculate_anion_gap(140, 104, 24)
    assert result["ag"] == 12.0


def test_enrichment_re_exports_winters():
    """Verify enrichment module re-exports Winter's formula."""
    result = winters_formula(10)
    assert result["expected_pco2"] == 23.0


def test_enrichment_re_exports_delta_ratio():
    """Verify enrichment module re-exports delta ratio."""
    result = calculate_delta_ratio(30.0, 10.0)
    assert result["delta_ratio"] is not None
    assert result["delta_ratio"] > 1.0


def test_enrichment_interpret_row():
    """Verify enrichment module re-exports interpret_row."""
    row = {"pH": "7.25", "pco2": "20", "hco3": "10", "na": "140", "cl": "100"}
    result = interpret_row(row)
    assert result["primary_disorder"] == "metabolic acidosis"
