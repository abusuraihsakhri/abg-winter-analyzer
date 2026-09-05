# Arterial Blood Gas (ABG) & Winter's Formula Analyzer

A Python clinical acid-base interpretation library and CLI tool. Evaluates arterial blood gas values, anion gap, compensation mechanisms, delta-delta ratios, mixed disorders, and differential diagnoses using standard clinical formulas.

Requires Python standard library only (zero external runtime dependencies).

---

## Features

- **Full ABG Interpretation:** Classifies arterial pH, $\text{pCO}_2$, and $\text{HCO}_3$ into primary disorders (metabolic/respiratory acidosis and alkalosis, fully compensated states, and mixed disorders).
- **Winter's Formula:** Evaluates respiratory compensation in metabolic acidosis:
  $$\text{Expected pCO}_2 = 1.5 \times \text{HCO}_3 + 8 \pm 2\text{ mmHg}$$
- **Anion Gap & Albumin Correction:** Calculates standard and potassium-corrected anion gap, as well as albumin-adjusted anion gap using the Figge formulation:
  $$\text{AG} = \text{Na}^+ - (\text{Cl}^- + \text{HCO}_3^-)$$
  $$\text{AG}_{\text{corrected}} = \text{AG} + 2.5 \times (4.0 - \text{Albumin})$$
- **Delta-Delta (Delta Ratio):** Identifies concurrent metabolic disorders in anion-gap metabolic acidosis:
  $$\Delta\text{-}\text{Ratio} = \frac{\text{AG} - 12}{24 - \text{HCO}_3}$$
- **Mixed Disorder Detection:** Multi-pathway compensation verification across acute and chronic respiratory disorders and metabolic alkalosis.
- **MUDPILES Differential Diagnosis:** Ranked differential diagnoses for elevated anion gap based on laboratory markers (lactate, glucose, BUN, etc.).
- **Batch Processing:** High-throughput batch processing of CSV records.
- **Input Validation:** All clinical values are validated against physiologically plausible ranges to prevent garbage-in-garbage-out errors.
- **Secure File Handling:** CSV processing includes path traversal protection and proper error handling.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies. `pytest` is optional for running tests.

```bash
git clone https://github.com/abusuraihsakhri/abg-winter-analyzer.git
cd abg-winter-analyzer
```

---

## CLI Usage

### 1. Full ABG Interpretation
```bash
python cli.py interpret --ph 7.25 --pco2 20 --hco3 10 --na 140 --cl 100
```
Output as JSON:
```bash
python cli.py interpret --ph 7.25 --pco2 20 --hco3 10 --na 140 --cl 100 --json
```

### 2. Winter's Formula Calculation
Calculate expected $\text{pCO}_2$ or evaluate compensation:
```bash
python cli.py winters --hco3 10
python cli.py winters --hco3 10 --pco2 25
```

### 3. Anion Gap Calculation
```bash
python cli.py anion-gap --na 140 --cl 100 --hco3 10
python cli.py anion-gap --na 140 --cl 100 --hco3 10 --k 4.0
```

### 4. Delta-Delta Ratio
```bash
python cli.py delta-ratio --na 140 --cl 100 --hco3 10
```

### 5. Batch CSV Processing
```bash
python cli.py batch --input sample.csv --output results.csv
```

---

## Python API Quickstart

```python
from abg_winter import interpret_abg, winters_formula, calculate_anion_gap
from abg_disorders import MixedDisorderDetector, AnionGapDifferential

# 1. Full interpretation
result = interpret_abg(ph=7.25, pco2=20.0, hco3=10.0, na=140.0, cl=100.0)
print(result["primary_disorder"])   # "metabolic acidosis"
print(result["clinical_summary"])

# 2. Mixed disorder detection
detector = MixedDisorderDetector()
report = detector.detect(ph=7.25, pco2=20.0, hco3=10.0, na=140.0, cl=100.0, albumin=4.0)
print(report.narrative)

# 3. Anion gap differential diagnosis
diff = AnionGapDifferential()
causes = diff.diagnose(ag=28.0, lactate=6.5)
for item in causes[:3]:
    print(f"- {item['cause']}: score {item['score']} ({item['workup']})")
```

## Input Validation

All clinical values are validated against physiologically plausible ranges to prevent invalid inputs from producing misleading results:

| Parameter | Valid Range |
|-----------|-------------|
| pH | 6.8 – 7.8 |
| pCO₂ | 5 – 120 mmHg |
| HCO₃ | 1 – 60 mEq/L |
| Na⁺ | 100 – 180 mEq/L |
| Cl⁻ | 60 – 140 mEq/L |
| K⁺ | 1 – 10 mEq/L |
| Albumin | 0.5 – 7 g/dL |

Invalid values raise `ABGValidationError` (from `abg_winter` module). Non-numeric inputs raise `TypeError`.

---

## Running Tests

Run the test suite via standard `unittest` or `pytest`:

```bash
# Using standard Python unittest
python -m unittest discover

# Using pytest
pytest -v
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
