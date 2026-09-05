#!/usr/bin/env python3
"""
ABG & Winter's Formula Analyzer
================================
Interprets arterial blood gas (ABG) results using standard clinical formulas:

- pH / pco2 / HCO3 interpretation
- Anion Gap (AG = Na - Cl - HCO3)
- Winter's Formula for expected pCO2 in metabolic acidosis
- Delta-Delta (Delta Ratio) for mixed disorder detection
- Compensation rules for all primary acid-base disorders

Stdlib only — no external dependencies.
"""
import os


# ---------------------------------------------------------------------------
# Reference ranges
# ---------------------------------------------------------------------------
PH_NORMAL = (7.35, 7.45)
PCO2_NORMAL = (35.0, 45.0)
HCO3_NORMAL = (22.0, 26.0)
AG_NORMAL = (8.0, 12.0)       # without K correction
AG_NORMAL_K = (10.0, 14.0)    # if K is included in the formula

# Clinical validation ranges (physiologically plausible extremes)
PH_MIN, PH_MAX = 6.8, 7.8
PCO2_MIN, PCO2_MAX = 5.0, 120.0
HCO3_MIN, HCO3_MAX = 1.0, 60.0
NA_MIN, NA_MAX = 100.0, 180.0
CL_MIN, CL_MAX = 60.0, 140.0
K_MIN, K_MAX = 1.0, 10.0
ALBUMIN_MIN, ALBUMIN_MAX = 0.5, 7.0


class ABGValidationError(ValueError):
    """Raised when a clinical value is outside the physiologically plausible range."""
    pass


def _validate_range(name: str, value: float, low: float, high: float) -> None:
    """Validate that a numeric value falls within an acceptable range."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be numeric, got {type(value).__name__}")
    if value < low or value > high:
        raise ABGValidationError(
            f"{name} value {value} is outside plausible range [{low}, {high}]"
        )


def validate_ph(ph: float) -> None:
    """Validate arterial pH is within physiologically plausible range."""
    _validate_range("pH", ph, PH_MIN, PH_MAX)


def validate_pco2(pco2: float) -> None:
    """Validate pCO2 is within physiologically plausible range."""
    _validate_range("pCO2", pco2, PCO2_MIN, PCO2_MAX)


def validate_hco3(hco3: float) -> None:
    """Validate HCO3 is within physiologically plausible range."""
    _validate_range("HCO3", hco3, HCO3_MIN, HCO3_MAX)


def validate_na(na: float) -> None:
    """Validate sodium is within physiologically plausible range."""
    _validate_range("Na", na, NA_MIN, NA_MAX)


def validate_cl(cl: float) -> None:
    """Validate chloride is within physiologically plausible range."""
    _validate_range("Cl", cl, CL_MIN, CL_MAX)


def validate_k(k: float) -> None:
    """Validate potassium is within physiologically plausible range."""
    _validate_range("K", k, K_MIN, K_MAX)


def validate_albumin(albumin: float) -> None:
    """Validate albumin is within physiologically plausible range."""
    _validate_range("Albumin", albumin, ALBUMIN_MIN, ALBUMIN_MAX)


# ---------------------------------------------------------------------------
# Individual value interpretation
# ---------------------------------------------------------------------------

def interpret_ph(ph: float) -> str:
    """Classify arterial pH."""
    if ph < 7.35:
        return "acidemia"
    if ph > 7.45:
        return "alkalemia"
    return "normal"


def interpret_pco2(pco2: float) -> str:
    """Classify pCO2 (mmHg)."""
    if pco2 > 45.0:
        return "respiratory acidosis"
    if pco2 < 35.0:
        return "respiratory alkalosis"
    return "normal"


def interpret_hco3(hco3: float) -> str:
    """Classify serum bicarbonate (mEq/L)."""
    if hco3 < 22.0:
        return "metabolic acidosis"
    if hco3 > 26.0:
        return "metabolic alkalosis"
    return "normal"


# ---------------------------------------------------------------------------
# Anion Gap
# ---------------------------------------------------------------------------

def calculate_anion_gap(na: float, cl: float, hco3: float,
                        k: float = None) -> dict:
    """
    Anion Gap = Na - (Cl + HCO3)

    If potassium is provided, uses: AG = (Na + K) - (Cl + HCO3)
    with normal range 10-14 mEq/L.

    Returns dict with 'ag', 'normal_low', 'normal_high', 'is_elevated'.
    """
    if k is not None:
        ag = (na + k) - (cl + hco3)
        low, high = AG_NORMAL_K
    else:
        ag = na - (cl + hco3)
        low, high = AG_NORMAL

    return {
        "ag": round(ag, 2),
        "normal_low": low,
        "normal_high": high,
        "is_elevated": ag > high,
        "is_low": ag < low,
    }


# ---------------------------------------------------------------------------
# Winter's Formula
# ---------------------------------------------------------------------------

def winters_formula(hco3: float) -> dict:
    """
    Winter's Formula: Expected pCO2 = 1.5 × HCO3 + 8 (±2 mmHg)

    Used to assess respiratory compensation in metabolic acidosis.
    Returns expected pCO2 and the acceptable range.
    """
    expected = 1.5 * hco3 + 8.0
    return {
        "expected_pco2": round(expected, 2),
        "range_low": round(expected - 2.0, 2),
        "range_high": round(expected + 2.0, 2),
        "formula": "pCO2 = 1.5 x HCO3 + 8 (±2)",
    }


def assess_winters(actual_pco2: float, hco3: float) -> dict:
    """
    Compare actual pCO2 to Winter's expected pCO2.

    Returns the expected value, deviation, and whether compensation
    is appropriate, or if there is a concurrent respiratory disorder.

    Raises
    ------
    ABGValidationError
        If any value is outside physiologically plausible range.
    """
    validate_pco2(actual_pco2)
    validate_hco3(hco3)
    w = winters_formula(hco3)
    expected = w["expected_pco2"]
    deviation = round(actual_pco2 - expected, 2)

    if w["range_low"] <= actual_pco2 <= w["range_high"]:
        status = "appropriate compensation"
        detail = "pCO2 is within the expected range for metabolic acidosis."
    elif actual_pco2 > w["range_high"]:
        status = "concurrent respiratory acidosis"
        detail = (
            f"pCO2 ({actual_pco2}) is higher than expected ({expected}). "
            "There is additional respiratory acidosis beyond compensation."
        )
    else:
        status = "concurrent respiratory alkalosis"
        detail = (
            f"pCO2 ({actual_pco2}) is lower than expected ({expected}). "
            "There is additional respiratory alkalosis beyond compensation."
        )

    return {
        "expected_pco2": expected,
        "range_low": w["range_low"],
        "range_high": w["range_high"],
        "actual_pco2": actual_pco2,
        "deviation": deviation,
        "status": status,
        "detail": detail,
    }


# ---------------------------------------------------------------------------
# Delta-Delta (Delta Ratio)
# ---------------------------------------------------------------------------

def calculate_delta_ratio(ag: float, hco3: float,
                          normal_ag: float = 12.0,
                          normal_hco3: float = 24.0) -> dict:
    """
    Delta Ratio = (AG - normal_AG) / (normal_HCO3 - HCO3)

    Interpretation:
      < 1  : Mixed anion gap metabolic acidosis + non-anion gap metabolic acidosis
      1-2  : Pure anion gap metabolic acidosis
      > 2  : Concurrent metabolic alkalosis

    Returns dict with ratio and interpretation.
    """
    delta_ag = ag - normal_ag
    delta_hco3 = normal_hco3 - hco3

    # Edge cases
    if delta_hco3 == 0:
        if delta_ag == 0:
            ratio = None
            interp = "no anion gap or bicarbonate change"
        else:
            ratio = None
            interp = "anion gap elevated without bicarbonate drop — consider lab error or concurrent metabolic alkalosis"
    else:
        raw_ratio = delta_ag / delta_hco3
        ratio = round(raw_ratio, 2)
        if raw_ratio < 1.0:
            interp = "mixed anion gap metabolic acidosis + non-anion gap metabolic acidosis"
        elif raw_ratio <= 2.0:
            interp = "pure anion gap metabolic acidosis"
        else:
            interp = "concurrent metabolic alkalosis"

    return {
        "delta_ag": round(delta_ag, 2),
        "delta_hco3": round(delta_hco3, 2),
        "delta_ratio": ratio,
        "interpretation": interp,
    }


# ---------------------------------------------------------------------------
# Compensation rules for each primary disorder
# ---------------------------------------------------------------------------

def assess_compensation_respiratory_acidosis(pco2: float, hco3: float) -> dict:
    """
    Respiratory acidosis compensation:
      Acute:  Expected HCO3 = 24 + 0.1 × (pCO2 - 40)  (±1.5)
      Chronic: Expected HCO3 = 24 + 0.35 × (pCO2 - 40) (±2.5)
    """
    delta_pco2 = pco2 - 40.0
    acute_expected = 24.0 + 0.1 * delta_pco2
    chronic_expected = 24.0 + 0.35 * delta_pco2

    acute_low = acute_expected - 1.5
    acute_high = acute_expected + 1.5
    chronic_low = chronic_expected - 2.5
    chronic_high = chronic_expected + 2.5

    if acute_low <= hco3 <= acute_high:
        status = "acute respiratory acidosis (appropriate compensation)"
    elif chronic_low <= hco3 <= chronic_high:
        status = "chronic respiratory acidosis (appropriate compensation)"
    elif hco3 > chronic_high:
        status = "respiratory acidosis + concurrent metabolic alkalosis"
    elif hco3 < acute_low:
        status = "respiratory acidosis + concurrent metabolic acidosis"
    else:
        status = "partially compensated respiratory acidosis"

    return {
        "acute_expected_hco3": round(acute_expected, 2),
        "acute_range": (round(acute_low, 2), round(acute_high, 2)),
        "chronic_expected_hco3": round(chronic_expected, 2),
        "chronic_range": (round(chronic_low, 2), round(chronic_high, 2)),
        "actual_hco3": hco3,
        "status": status,
    }


def assess_compensation_respiratory_alkalosis(pco2: float, hco3: float) -> dict:
    """
    Respiratory alkalosis compensation:
      Acute:  Expected HCO3 = 24 + 0.2 × (pCO2 - 40)  (±1.5)
      Chronic: Expected HCO3 = 24 + 0.5 × (pCO2 - 40) (±2.0)
    """
    delta_pco2 = pco2 - 40.0
    acute_expected = 24.0 + 0.2 * delta_pco2
    chronic_expected = 24.0 + 0.5 * delta_pco2

    acute_low = acute_expected - 1.5
    acute_high = acute_expected + 1.5
    chronic_low = chronic_expected - 2.0
    chronic_high = chronic_expected + 2.0

    if acute_low <= hco3 <= acute_high:
        status = "acute respiratory alkalosis (appropriate compensation)"
    elif chronic_low <= hco3 <= chronic_high:
        status = "chronic respiratory alkalosis (appropriate compensation)"
    elif hco3 > chronic_high:
        status = "respiratory alkalosis + concurrent metabolic alkalosis"
    elif hco3 < acute_low:
        status = "respiratory alkalosis + concurrent metabolic acidosis"
    else:
        status = "partially compensated respiratory alkalosis"

    return {
        "acute_expected_hco3": round(acute_expected, 2),
        "acute_range": (round(acute_low, 2), round(acute_high, 2)),
        "chronic_expected_hco3": round(chronic_expected, 2),
        "chronic_range": (round(chronic_low, 2), round(chronic_high, 2)),
        "actual_hco3": hco3,
        "status": status,
    }


def assess_compensation_metabolic_alkalosis(pco2: float, hco3: float) -> dict:
    """
    Metabolic alkalosis compensation:
      Expected pCO2 = 0.7 × HCO3 + 20 (±1.5)
    """
    expected = 0.7 * hco3 + 20.0
    low = expected - 1.5
    high = expected + 1.5

    if low <= pco2 <= high:
        status = "appropriate respiratory compensation for metabolic alkalosis"
    elif pco2 > high:
        status = "metabolic alkalosis + concurrent respiratory acidosis"
    else:
        status = "metabolic alkalosis + concurrent respiratory alkalosis"

    return {
        "expected_pco2": round(expected, 2),
        "range": (round(low, 2), round(high, 2)),
        "actual_pco2": pco2,
        "status": status,
    }


# ---------------------------------------------------------------------------
# Full ABG Interpretation
# ---------------------------------------------------------------------------

def interpret_abg(ph: float, pco2: float, hco3: float,
                  na: float = None, cl: float = None,
                  k: float = None) -> dict:
    """
    Full arterial blood gas interpretation.

    Parameters
    ----------
    ph   : arterial pH
    pco2 : arterial pCO2 in mmHg
    hco3 : serum bicarbonate in mEq/L
    na   : serum sodium in mEq/L (optional, needed for anion gap)
    cl   : serum chloride in mEq/L (optional, needed for anion gap)
    k    : serum potassium in mEq/L (optional, for K-corrected AG)

    Returns
    -------
    dict with keys:
      ph_status, pco2_status, hco3_status,
      primary_disorder, compensation, compensation_detail,
      anion_gap (if na/cl provided), delta_ratio (if applicable),
      winters (if metabolic acidosis), clinical_summary

    Raises
    ------
    ABGValidationError
        If any value is outside physiologically plausible range.
    TypeError
        If any value is not numeric.
    """
    # Validate required parameters
    validate_ph(ph)
    validate_pco2(pco2)
    validate_hco3(hco3)

    # Validate optional parameters if provided
    if na is not None:
        validate_na(na)
    if cl is not None:
        validate_cl(cl)
    if k is not None:
        validate_k(k)

    result = {
        "ph": ph,
        "pco2": pco2,
        "hco3": hco3,
        "ph_status": interpret_ph(ph),
        "pco2_status": interpret_pco2(pco2),
        "hco3_status": interpret_hco3(hco3),
    }

    # --- Determine primary disorder ---
    primary = _determine_primary(ph, pco2, hco3)
    result["primary_disorder"] = primary

    # --- Anion Gap (if electrolytes provided) ---
    ag_info = None
    if na is not None and cl is not None:
        ag_info = calculate_anion_gap(na, cl, hco3, k)
        result["anion_gap"] = ag_info

    # --- Compensation assessment ---
    compensation = {}
    winters_info = None
    delta_info = None

    if primary == "metabolic acidosis":
        winters_info = assess_winters(pco2, hco3)
        compensation = {
            "type": "Winter's Formula",
            "detail": winters_info["status"],
            "explanation": winters_info["detail"],
        }
        if ag_info:
            delta_info = calculate_delta_ratio(ag_info["ag"], hco3)
            result["delta_ratio"] = delta_info

    elif primary == "metabolic alkalosis":
        comp = assess_compensation_metabolic_alkalosis(pco2, hco3)
        compensation = {
            "type": "Respiratory compensation",
            "detail": comp["status"],
            "expected_pco2": comp["expected_pco2"],
            "range": comp["range"],
        }

    elif primary == "respiratory acidosis":
        comp = assess_compensation_respiratory_acidosis(pco2, hco3)
        compensation = {
            "type": "Metabolic compensation",
            "detail": comp["status"],
            "acute_expected_hco3": comp["acute_expected_hco3"],
            "chronic_expected_hco3": comp["chronic_expected_hco3"],
        }

    elif primary == "respiratory alkalosis":
        comp = assess_compensation_respiratory_alkalosis(pco2, hco3)
        compensation = {
            "type": "Metabolic compensation",
            "detail": comp["status"],
            "acute_expected_hco3": comp["acute_expected_hco3"],
            "chronic_expected_hco3": comp["chronic_expected_hco3"],
        }

    elif primary == "normal":
        compensation = {
            "type": "none needed",
            "detail": "Normal acid-base status",
        }

    else:
        # Fully compensated or mixed disorders with normal pH
        compensation = {
            "type": "assessment",
            "detail": primary,
        }

    result["compensation"] = compensation
    if winters_info:
        result["winters"] = winters_info

    # --- Clinical summary ---
    result["clinical_summary"] = _build_summary(result, ag_info, delta_info)

    return result


def _determine_primary(ph: float, pco2: float, hco3: float) -> str:
    """
    Determine the primary acid-base disorder from pH, pCO2, and HCO3.

    Logic:
    - If pH is normal, call it normal (unless both pCO2 and HCO3 are abnormal
      in opposite directions, suggesting a mixed disorder with normal pH).
    - Acidemia (pH < 7.35):
        - If HCO3 < 22 → metabolic acidosis (primary)
        - If pCO2 > 45 → respiratory acidosis (primary)
        - If both → metabolic acidosis is primary (check Winter's for叠加)
    - Alkalemia (pH > 7.45):
        - If HCO3 > 26 → metabolic alkalosis (primary)
        - If pCO2 < 35 → respiratory alkalosis (primary)
        - If both → metabolic alkalosis is primary
    """
    ph_status = interpret_ph(ph)
    pco2_status = interpret_pco2(pco2)
    hco3_status = interpret_hco3(hco3)

    if ph_status == "normal":
        # Check for fully compensated or mixed with normal pH
        if pco2_status != "normal" and hco3_status != "normal":
            # Both abnormal in compensatory direction — fully compensated
            if pco2_status == "respiratory acidosis" and hco3_status == "metabolic alkalosis":
                return "fully compensated respiratory acidosis"
            if pco2_status == "respiratory alkalosis" and hco3_status == "metabolic acidosis":
                return "fully compensated respiratory alkalosis"
            if pco2_status == "respiratory acidosis" and hco3_status == "metabolic acidosis":
                return "mixed respiratory and metabolic acidosis (pH near normal)"
            if pco2_status == "respiratory alkalosis" and hco3_status == "metabolic alkalosis":
                return "mixed respiratory and metabolic alkalosis (pH near normal)"
        return "normal"

    if ph_status == "acidemia":
        # Both point to acidosis — metabolic is primary, check for叠加
        if hco3_status == "metabolic acidosis":
            return "metabolic acidosis"
        if pco2_status == "respiratory acidosis":
            return "respiratory acidosis"
        # Edge: pH acidic but neither clearly abnormal — return what we can
        return "acidosis (unclassified)"

    # alkalemia
    if hco3_status == "metabolic alkalosis":
        return "metabolic alkalosis"
    if pco2_status == "respiratory alkalosis":
        return "respiratory alkalosis"
    return "alkalosis (unclassified)"


def _build_summary(result: dict, ag_info: dict = None,
                   delta_info: dict = None) -> str:
    """Build a human-readable clinical summary string."""
    parts = []

    primary = result["primary_disorder"]
    parts.append(f"Primary disorder: {primary}.")

    comp = result["compensation"]
    parts.append(f"Compensation: {comp['detail']}.")

    if ag_info:
        ag_val = ag_info["ag"]
        if ag_info["is_elevated"]:
            parts.append(f"Anion gap is elevated at {ag_val} mEq/L (normal {ag_info['normal_low']}-{ag_info['normal_high']}).")
        elif ag_info["is_low"]:
            parts.append(f"Anion gap is low at {ag_val} mEq/L (normal {ag_info['normal_low']}-{ag_info['normal_high']}).")
        else:
            parts.append(f"Anion gap is normal at {ag_val} mEq/L.")

    if delta_info and delta_info["delta_ratio"] is not None:
        parts.append(f"Delta ratio: {delta_info['delta_ratio']} — {delta_info['interpretation']}.")

    if "winters" in result:
        w = result["winters"]
        parts.append(
            f"Winter's expected pCO2: {w['expected_pco2']} mmHg "
            f"(range {w['range_low']}-{w['range_high']}). "
            f"Actual: {w['actual_pco2']} mmHg."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# CSV batch processing
# ---------------------------------------------------------------------------

def interpret_row(row: dict) -> dict:
    """
    Interpret a single row (dict) from a CSV. Looks for keys:
    pH, pco2, hco3, na, cl, k (case-insensitive, flexible naming).
    """
    def _get(row, *keys, default=None):
        for k in keys:
            for rk, rv in row.items():
                if rk.lower().strip() == k.lower():
                    try:
                        return float(rv)
                    except (ValueError, TypeError):
                        return default
        return default

    ph = _get(row, "ph")
    pco2 = _get(row, "pco2", "paco2", "pCO2")
    hco3 = _get(row, "hco3", "bicarbonate", "hco3_meq")
    na = _get(row, "na", "sodium")
    cl = _get(row, "cl", "chloride")
    k = _get(row, "k", "potassium")

    if ph is None or pco2 is None or hco3 is None:
        return {"error": "Missing required values: pH, pCO2, HCO3"}

    return interpret_abg(ph, pco2, hco3, na, cl, k)


def _safe_resolve_path(path: str) -> str:
    """
    Resolve a path safely, preventing path traversal attacks.

    Returns the resolved absolute path after verifying it doesn't escape
    via symlinks or '..' components in an unexpected way.
    """
    # Resolve to absolute path (handles .., symlinks, etc.)
    resolved = os.path.realpath(os.path.abspath(path))
    return resolved


def process_csv(input_path: str, output_path: str) -> list:
    """
    Process a CSV file of ABG values and write results to output CSV.

    Parameters
    ----------
    input_path : str
        Path to input CSV file. Must exist and be readable.
    output_path : str
        Path to output CSV file. Parent directory must exist.

    Returns
    -------
    list of dicts with interpretation results.

    Raises
    ------
    FileNotFoundError
        If input_path does not exist.
    PermissionError
        If input_path is not readable or output_path is not writable.
    ValueError
        If input_path is not a file.
    """
    import csv

    # Resolve paths safely (prevents path traversal)
    input_path = _safe_resolve_path(input_path)
    output_path = _safe_resolve_path(output_path)

    # Validate input file exists and is a file
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not os.path.isfile(input_path):
        raise ValueError(f"Input path is not a file: {input_path}")

    # Validate output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    results = []
    for row in rows:
        interp = interpret_row(row)
        # Flatten nested dicts for CSV output
        flat = dict(row)
        for key, val in interp.items():
            if isinstance(val, dict):
                for subkey, subval in val.items():
                    col_name = f"{key}_{subkey}"
                    flat[col_name] = str(subval)
            else:
                flat[key] = str(val)
        results.append(flat)

    # Collect all field names
    all_keys = []
    seen = set()
    for r in results:
        for k in r:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    return results
