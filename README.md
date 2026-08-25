# ABG & Winter's Formula Analyzer

A command-line tool for interpreting arterial blood gas (ABG) results using standard clinical formulas. No external dependencies — pure Python stdlib.

## What It Does

Given ABG values (pH, pCO2, HCO3) and optional electrolytes (Na, Cl, K), this tool determines:

1. **Primary acid-base disorder** — acidemia/alkalemia classification and whether the primary disturbance is metabolic or respiratory
2. **Compensation status** — whether the body's compensatory response is appropriate, or if there is a叠加 (superimposed) second disorder
3. **Anion Gap** — `AG = Na - (Cl + HCO3)`, with optional potassium correction
4. **Winter's Formula** — expected pCO2 in metabolic acidosis: `pCO2 = 1.5 × HCO3 + 8 (±2)`
5. **Delta-Delta Ratio** — `(AG - 12) / (24 - HCO3)` to detect mixed disorders

## Formulas Implemented

### Anion Gap
```
AG = Na - (Cl + HCO3)          Normal: 8-12 mEq/L
AG = (Na + K) - (Cl + HCO3)   Normal: 10-14 mEq/L (with K)
```

### Winter's Formula (Metabolic Acidosis Compensation)
```
Expected pCO2 = 1.5 × HCO3 + 8  (±2 mmHg)
```
- Actual pCO2 within range → appropriate respiratory compensation
- Actual pCO2 higher than expected → concurrent respiratory acidosis
- Actual pCO2 lower than expected → concurrent respiratory alkalosis

### Delta-Delta Ratio
```
Delta Ratio = (AG - 12) / (24 - HCO3)
```
| Ratio | Interpretation |
|-------|---------------|
| < 1 | Mixed anion gap metabolic acidosis + non-anion gap metabolic acidosis |
| 1-2 | Pure anion gap metabolic acidosis |
| > 2 | Concurrent metabolic alkalosis |

### Respiratory Acidosis Compensation
```
Acute:   Expected HCO3 = 24 + 0.1 × (pCO2 - 40)   (±1.5)
Chronic: Expected HCO3 = 24 + 0.35 × (pCO2 - 40)  (±2.5)
```

### Respiratory Alkalosis Compensation
```
Acute:   Expected HCO3 = 24 + 0.2 × (pCO2 - 40)   (±1.5)
Chronic: Expected HCO3 = 24 + 0.5 × (pCO2 - 40)   (±2.0)
```

### Metabolic Alkalosis Compensation
```
Expected pCO2 = 0.7 × HCO3 + 20  (±1.5)
```

## CLI Usage

### Full ABG Interpretation
```bash
python cli.py interpret --pH 7.25 --pco2 20 --hco3 10 --na 140 --cl 100
```

Output:
```
============================================================
  ABG INTERPRETATION
============================================================
  pH:    7.25   (acidemia)
  pCO2:  20.0 mmHg  (respiratory alkalosis)
  HCO3:  10.0 mEq/L  (metabolic acidosis)

  Primary disorder: metabolic acidosis
  Compensation: concurrent respiratory alkalosis
  Anion Gap: 30.0 mEq/L (normal 8.0-12.0)
    ** ELEVATED **
  Delta Ratio: 1.29
    pure anion gap metabolic acidosis

  Winter's Formula:
    Expected pCO2: 23.0 mmHg (range 21.0-25.0)
    Actual pCO2: 20.0 mmHg
    Deviation: -3.0 mmHg
    Assessment: concurrent respiratory alkalosis
============================================================
```

### Winter's Formula Only
```bash
# Calculate expected pCO2
python cli.py winters --hco3 10

# Assess actual pCO2 against expected
python cli.py winters --hco3 10 --pco2 20
```

### Anion Gap
```bash
python cli.py anion-gap --na 140 --cl 100 --hco3 10
python cli.py anion-gap --na 140 --cl 100 --hco3 10 --k 4.0
```

### Delta-Delta Ratio
```bash
python cli.py delta-ratio --na 140 --cl 100 --hco3 10
```

### JSON Output
Add `--json` to any command for machine-readable output:
```bash
python cli.py interpret --pH 7.25 --pco2 20 --hco3 10 --na 140 --cl 100 --json
```

### Batch Processing
Process a CSV file of ABG values:
```bash
python cli.py batch --input sample.csv --output results.csv
```

Input CSV columns: `pH`, `pco2`, `hco3`, `na`, `cl`, `k` (case-insensitive)

## Python API

```python
from abg_winter import interpret_abg, calculate_anion_gap, winters_formula

# Full interpretation
result = interpret_abg(ph=7.25, pco2=20, hco3=10, na=140, cl=100)
print(result["primary_disorder"])   # "metabolic acidosis"
print(result["anion_gap"]["ag"])    # 30.0
print(result["winters"]["status"])  # "concurrent respiratory alkalosis"

# Individual calculations
ag = calculate_anion_gap(na=140, cl=100, hco3=10)
w = winters_formula(hco3=10)
```

## Running Tests

```bash
python -m pytest test_abg_winter.py -v
# or
python test_abg_winter.py
```

## Input/Output Format

### CLI Input
| Parameter | Unit | Required | Description |
|-----------|------|----------|-------------|
| `--ph` | — | Yes | Arterial pH |
| `--pco2` | mmHg | Yes | Arterial pCO2 |
| `--hco3` | mEq/L | Yes | Serum bicarbonate |
| `--na` | mEq/L | No | Serum sodium |
| `--cl` | mEq/L | No | Serum chloride |
| `--k` | mEq/L | No | Serum potassium |

### JSON Output Keys
- `ph`, `pco2`, `hco3` — input values
- `ph_status`, `pco2_status`, `hco3_status` — individual interpretations
- `primary_disorder` — identified primary acid-base disorder
- `compensation` — compensation assessment with details
- `anion_gap` — anion gap calculation (if Na/Cl provided)
- `delta_ratio` — delta-delta analysis (if anion gap calculable)
- `winters` — Winter's Formula results (if metabolic acidosis)
- `clinical_summary` — human-readable summary

## Clinical Reference

This tool implements standard acid-base physiology formulas as taught in medical education and used in clinical practice. The formulas are based on:

- **Winter's Formula**: Winter SD, Lowder JH, Bhatt KN. *Predictive value of the pCO2 in metabolic acidosis.* Am J Kidney Dis. 1987.
- **Anion Gap**: Emmett M, Narins RG. *Clinical use of the anion gap.* Medicine. 1977.
- **Compensation rules**: Based on standard clinical physiology references (Harrison's, Sabatine Pocket Medicine).

**Disclaimer**: This is an educational/clinical reference tool. It does not replace clinical judgment. Always correlate with the full clinical picture.

## License

MIT License. See [LICENSE](LICENSE) for details.
