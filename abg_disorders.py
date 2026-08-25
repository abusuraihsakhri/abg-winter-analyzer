#!/usr/bin/env python3
"""
Mixed Acid-Base Disorder Detection & Anion Gap Differential Diagnosis.

Companion module to abg_winter.py — provides higher-level disorder
detection and differential diagnosis for elevated anion gap.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional

from abg_winter import (
    calculate_anion_gap,
    assess_winters,
    assess_compensation_respiratory_acidosis,
    assess_compensation_respiratory_alkalosis,
    assess_compensation_metabolic_alkalosis,
    interpret_ph,
    interpret_pco2,
    interpret_hco3,
)


@dataclass
class AcidBaseDisorder:
    """A detected acid-base disorder with evidence."""
    name: str
    confidence: float       # 0-1
    contribution: float     # 0-1 scale
    evidence: List[str] = field(default_factory=list)
    compensation_formula: str = ""
    expected_range: tuple = (0.0, 0.0)


@dataclass
class MixedDisorderReport:
    """Report from mixed disorder detection."""
    disorders: List[AcidBaseDisorder]
    anion_gap: float
    delta_gap: float
    delta_ratio: float
    primary_disorder: Optional[str]
    narrative: str


class MixedDisorderDetector:
    """
    Detects simultaneous multiple acid-base disorders.

    Uses compensation formulas to identify when the observed pCO2 or HCO3
    deviates from expected values, indicating a second (叠加) disorder.
    """

    def detect(self, ph: float, pco2: float, hco3: float,
               na: float = 140.0, cl: float = 102.0,
               albumin: float = 4.0) -> MixedDisorderReport:
        """
        Analyze ABG for mixed disorders.

        Parameters
        ----------
        ph : arterial pH
        pco2 : pCO2 in mmHg
        hco3 : HCO3 in mEq/L
        na : sodium in mEq/L
        cl : chloride in mEq/L
        albumin : albumin in g/dL (for corrected anion gap)

        Returns
        -------
        MixedDisorderReport with detected disorders and analysis.
        """
        disorders = []

        # Corrected anion gap for albumin
        corrected_cl = cl + 0.6 * (3.5 - albumin) if albumin else cl
        ag = na - corrected_cl - hco3
        delta_gap = ag - 12.0

        # Avoid division by zero
        if hco3 != 24:
            delta_ratio = abs(delta_gap) / abs(hco3 - 24)
        else:
            delta_ratio = float('inf') if delta_gap != 0 else 0.0

        ph_status = interpret_ph(ph)
        pco2_status = interpret_pco2(pco2)
        hco3_status = interpret_hco3(hco3)

        # --- Detect primary and secondary disorders ---

        if ph_status == "acidemia":
            if hco3_status == "metabolic acidosis":
                disorders.append(self._detect_metabolic_acidosis(pco2, hco3, ag))
            if pco2_status == "respiratory acidosis":
                disorders.append(self._detect_respiratory_acidosis(pco2, hco3))
        elif ph_status == "alkalemia":
            if hco3_status == "metabolic alkalosis":
                disorders.append(self._detect_metabolic_alkalosis(pco2, hco3))
            if pco2_status == "respiratory alkalosis":
                disorders.append(self._detect_respiratory_alkalosis(pco2, hco3))
        else:
            # Normal pH — check for compensated or mixed disorders
            if pco2_status == "respiratory acidosis" and hco3_status == "metabolic alkalosis":
                disorders.append(AcidBaseDisorder(
                    name="Fully compensated respiratory acidosis",
                    confidence=0.8,
                    contribution=0.5,
                    evidence=[f"Normal pH with elevated pCO2 ({pco2}) and HCO3 ({hco3})"],
                ))
            elif pco2_status == "respiratory alkalosis" and hco3_status == "metabolic acidosis":
                disorders.append(AcidBaseDisorder(
                    name="Fully compensated respiratory alkalosis",
                    confidence=0.8,
                    contribution=0.5,
                    evidence=[f"Normal pH with low pCO2 ({pco2}) and HCO3 ({hco3})"],
                ))
            elif pco2_status != "normal" and hco3_status != "normal":
                disorders.append(AcidBaseDisorder(
                    name="Mixed disorder (pH near normal)",
                    confidence=0.7,
                    contribution=0.5,
                    evidence=[f"Normal pH with abnormal pCO2 ({pco2}) and HCO3 ({hco3})"],
                ))

        disorders = [d for d in disorders if d is not None]
        primary = disorders[0].name if disorders else None

        narrative = self._build_narrative(ph, pco2, hco3, ag, delta_gap,
                                          delta_ratio, disorders)

        return MixedDisorderReport(
            disorders=disorders,
            anion_gap=round(ag, 2),
            delta_gap=round(delta_gap, 2),
            delta_ratio=round(delta_ratio, 2),
            primary_disorder=primary,
            narrative=narrative,
        )

    def _detect_metabolic_acidosis(self, pco2: float, hco3: float,
                                    ag: float) -> AcidBaseDisorder:
        w = assess_winters(pco2, hco3)
        evidence = [
            f"HCO3={hco3}, pCO2={pco2}",
            f"Winter's expected pCO2={w['expected_pco2']} (range {w['range_low']}-{w['range_high']})",
            f"Assessment: {w['status']}",
        ]
        if ag > 12:
            evidence.append(f"Elevated anion gap ({ag:.1f})")

        contribution = min(1.0, (24 - hco3) / 24)

        return AcidBaseDisorder(
            name="Metabolic acidosis",
            confidence=min(0.95, contribution + 0.3),
            contribution=contribution,
            evidence=evidence,
            compensation_formula="Winter's: pCO2 = 1.5 x HCO3 + 8 (±2)",
            expected_range=(w["range_low"], w["range_high"]),
        )

    def _detect_metabolic_alkalosis(self, pco2: float,
                                     hco3: float) -> AcidBaseDisorder:
        comp = assess_compensation_metabolic_alkalosis(pco2, hco3)
        evidence = [
            f"HCO3={hco3}, pCO2={pco2}",
            f"Expected pCO2={comp['expected_pco2']} (range {comp['range'][0]}-{comp['range'][1]})",
            f"Assessment: {comp['status']}",
        ]
        contribution = min(1.0, (hco3 - 24) / 24)

        return AcidBaseDisorder(
            name="Metabolic alkalosis",
            confidence=min(0.95, contribution + 0.3),
            contribution=contribution,
            evidence=evidence,
            compensation_formula="pCO2 = 0.7 x HCO3 + 20 (±1.5)",
            expected_range=comp["range"],
        )

    def _detect_respiratory_acidosis(self, pco2: float,
                                      hco3: float) -> AcidBaseDisorder:
        comp = assess_compensation_respiratory_acidosis(pco2, hco3)
        evidence = [
            f"pCO2={pco2}, HCO3={hco3}",
            f"Acute expected HCO3={comp['acute_expected_hco3']}",
            f"Chronic expected HCO3={comp['chronic_expected_hco3']}",
            f"Assessment: {comp['status']}",
        ]
        contribution = min(1.0, (pco2 - 40) / 40)

        return AcidBaseDisorder(
            name="Respiratory acidosis",
            confidence=min(0.95, contribution + 0.3),
            contribution=contribution,
            evidence=evidence,
            compensation_formula="Acute: HCO3 = 24 + 0.1*(pCO2-40); Chronic: HCO3 = 24 + 0.35*(pCO2-40)",
            expected_range=(comp["acute_range"][0], comp["chronic_range"][1]),
        )

    def _detect_respiratory_alkalosis(self, pco2: float,
                                       hco3: float) -> AcidBaseDisorder:
        comp = assess_compensation_respiratory_alkalosis(pco2, hco3)
        evidence = [
            f"pCO2={pco2}, HCO3={hco3}",
            f"Acute expected HCO3={comp['acute_expected_hco3']}",
            f"Chronic expected HCO3={comp['chronic_expected_hco3']}",
            f"Assessment: {comp['status']}",
        ]
        contribution = min(1.0, (40 - pco2) / 40)

        return AcidBaseDisorder(
            name="Respiratory alkalosis",
            confidence=min(0.95, contribution + 0.3),
            contribution=contribution,
            evidence=evidence,
            compensation_formula="Acute: HCO3 = 24 + 0.2*(pCO2-40); Chronic: HCO3 = 24 + 0.5*(pCO2-40)",
            expected_range=(comp["acute_range"][0], comp["chronic_range"][1]),
        )

    def _build_narrative(self, ph, pco2, hco3, ag, delta_gap,
                         delta_ratio, disorders) -> str:
        parts = [
            f"ABG: pH={ph:.2f}, pCO2={pco2:.1f}, HCO3={hco3:.1f}",
            f"Anion Gap={ag:.1f} (normal 12), Delta Gap={delta_gap:.1f}, Delta Ratio={delta_ratio:.2f}",
        ]
        if disorders:
            for d in disorders:
                parts.append(f"{d.name} (confidence {d.confidence:.0%})")
        else:
            parts.append("No acute acid-base disorder detected.")
        return "; ".join(parts)


class AnionGapDifferential:
    """
    Maps elevated anion gap to ranked differential diagnoses.

    Uses the mnemonic MUDPILES + causes:
    - M: Methanol
    - U: Uremia
    - D: Diabetic ketoacidosis
    - P: Propylene glycol / Paraldehyde
    - I: Isoniazid / Iron
    - L: Lactic acidosis
    - E: Ethylene glycol
    - S: Salicylates / Starvation
    """

    CAUSES = [
        {"name": "Lactic acidosis", "condition": lambda lactate, **kw: lactate and lactate > 4.0,
         "weight": 0.9, "workup": "Serum lactate, blood cultures, tissue perfusion assessment"},
        {"name": "Diabetic ketoacidosis", "condition": lambda glucose, **kw: glucose and glucose > 250,
         "weight": 0.85, "workup": "Blood glucose, serum ketones, urine ketones, VBG"},
        {"name": "Uremia", "condition": lambda bun, **kw: bun and bun > 60,
         "weight": 0.7, "workup": "BUN, creatinine, renal ultrasound"},
        {"name": "Methanol ingestion", "condition": lambda **kw: True,
         "weight": 0.5, "workup": "Osmol gap, methanol level, ethanol level"},
        {"name": "Ethylene glycol ingestion", "condition": lambda **kw: True,
         "weight": 0.5, "workup": "Osmol gap, ethylene glycol level, urine calcium oxalate crystals"},
        {"name": "Salicylate toxicity", "condition": lambda ph, **kw: ph and ph < 7.4,
         "weight": 0.5, "workup": "Salicylate level, arterial blood gas"},
        {"name": "Alcoholic ketoacidosis", "condition": lambda **kw: True,
         "weight": 0.6, "workup": "Serum ketones, alcohol level, glucose"},
        {"name": "Starvation ketosis", "condition": lambda **kw: True,
         "weight": 0.3, "workup": "Serum ketones, dietary history"},
    ]

    def diagnose(self, ag: float, ph: float = 7.4, lactate: float = None,
                 glucose: float = None, bun: float = None) -> List[Dict]:
        """
        Generate differential diagnosis for elevated anion gap.

        Parameters
        ----------
        ag : calculated anion gap
        ph : arterial pH
        lactate : serum lactate (mmol/L)
        glucose : blood glucose (mg/dL)
        bun : blood urea nitrogen (mg/dL)

        Returns
        -------
        List of dicts with cause, score, and workup.
        """
        if ag <= 12:
            return [{"cause": "Normal anion gap — no gap acidosis",
                     "score": 1.0, "workup": "Consider non-anion gap acidosis (diarrhea, RTA)"}]

        results = []
        for cause in self.CAUSES:
            score = cause["weight"]
            try:
                if cause["condition"](lactate=lactate, glucose=glucose,
                                       bun=bun, ph=ph):
                    score *= 1.2
            except (TypeError, KeyError):
                pass
            results.append({
                "cause": cause["name"],
                "score": round(min(1.0, score), 2),
                "workup": cause["workup"],
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results
