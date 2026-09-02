# Abg Winter Analyzer

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Mixed Acid-Base Disorder Detection & Anion Gap Differential Diagnosis.

Companion module to abg_winter.py — provides higher-level disorder
detection and differential diagnosis for elevated anion gap.

ABG & Winter's Formula Analyzer
================================
Interprets arterial blood gas (ABG) results using standard clinical formulas:

- pH / pCO2 / HCO3 interpretation
- Anion Gap (AG = Na - Cl - HCO3)
- Winter's Formula for expected pCO2 in metabolic acidosis
- Delta-Delta (Delta Ratio) for mixed disorder detection
- Compensation rules for all primary acid-base disorders

Stdlib only — no external dependencies.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`AcidBaseDisorder`**: A detected acid-base disorder with evidence.
- **`MixedDisorderReport`**: Report from mixed disorder detection.
- **`MixedDisorderDetector`**: Detects simultaneous multiple acid-base disorders.

Uses compensation formulas to identify when the observed pCO2 or HCO3
deviates from expected values, indicating a second (叠加) disorder.
- **`AnionGapDifferential`**: Maps elevated anion gap to ranked differential diagnoses.

Uses the mnemonic MUDPILES + causes:
- M: Methanol
- U: Uremia
- D: Diabetic ketoacidosis
- P: Propylene glycol / Paraldehyde
- I: Isoniazid / Iron
- L: Lactic acidosis
- E: Ethylene glycol
- S: Salicylates / Starvation

---

## 📐 Mathematical Formulation & Logic

```text
  calculate_anion_gap,
  compensation_formula: str = ""
  Uses compensation formulas to identify when the observed pCO2 or HCO3
  compensation_formula="Winter's: pCO2 = 1.5 x HCO3 + 8 (±2)",
  compensation_formula="pCO2 = 0.7 x HCO3 + 20 (±1.5)",
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --pH <value> --pco2 <value> --hco3 <value> --na <value>
```

### Parameter Reference
- `--pH`: Specifies input measurement or parameter value.
- `--pco2`: Specifies input measurement or parameter value.
- `--hco3`: Specifies input measurement or parameter value.
- `--na`: Specifies input measurement or parameter value.
- `--cl`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.
- `---`: Specifies input measurement or parameter value.
- `--ph`: Specifies input measurement or parameter value.
- `--k`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `pH` | Parameter / observation metric | Required |
| `pco2` | Parameter / observation metric | Required |
| `hco3` | Parameter / observation metric | Required |
| `na` | Parameter / observation metric | Required |
| `cl` | Parameter / observation metric | Required |
| `description` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t abg-winter-analyzer .
docker run -p 8000:8000 abg-winter-analyzer
```
