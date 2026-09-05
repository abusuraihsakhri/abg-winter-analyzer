"""
Enrichment module — re-exports core ABG functions for backward compatibility.

All real logic lives in abg_winter.py. This module provides convenience
aliases for programmatic use.
"""
from abg_winter import (
    interpret_abg,
    interpret_ph,
    interpret_pco2,
    interpret_hco3,
    calculate_anion_gap,
    winters_formula,
    assess_winters,
    calculate_delta_ratio,
    assess_compensation_respiratory_acidosis,
    assess_compensation_respiratory_alkalosis,
    assess_compensation_metabolic_alkalosis,
    interpret_row,
    process_csv,
    # Validation functions
    validate_ph,
    validate_pco2,
    validate_hco3,
    validate_na,
    validate_cl,
    validate_k,
    validate_albumin,
    ABGValidationError,
)

__all__ = [
    "interpret_abg",
    "interpret_ph",
    "interpret_pco2",
    "interpret_hco3",
    "calculate_anion_gap",
    "winters_formula",
    "assess_winters",
    "calculate_delta_ratio",
    "assess_compensation_respiratory_acidosis",
    "assess_compensation_respiratory_alkalosis",
    "assess_compensation_metabolic_alkalosis",
    "interpret_row",
    "process_csv",
    # Validation functions
    "validate_ph",
    "validate_pco2",
    "validate_hco3",
    "validate_na",
    "validate_cl",
    "validate_k",
    "validate_albumin",
    "ABGValidationError",
]
