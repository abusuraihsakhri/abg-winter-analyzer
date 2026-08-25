#!/usr/bin/env python3
"""
Tests for ABG & Winter's Formula Analyzer.

All test cases use known clinical examples with expected outputs.
"""
import unittest
from abg_winter import (
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
    interpret_abg,
    interpret_row,
)


class TestPHInterpretation(unittest.TestCase):
    """Test arterial pH classification."""

    def test_normal_low(self):
        self.assertEqual(interpret_ph(7.35), "normal")

    def test_normal_high(self):
        self.assertEqual(interpret_ph(7.45), "normal")

    def test_normal_mid(self):
        self.assertEqual(interpret_ph(7.40), "normal")

    def test_acidemia(self):
        self.assertEqual(interpret_ph(7.25), "acidemia")

    def test_severe_acidemia(self):
        self.assertEqual(interpret_ph(7.10), "acidemia")

    def test_alkalemia(self):
        self.assertEqual(interpret_ph(7.50), "alkalemia")

    def test_severe_alkalemia(self):
        self.assertEqual(interpret_ph(7.60), "alkalemia")

    def test_just_below_normal(self):
        self.assertEqual(interpret_ph(7.34), "acidemia")

    def test_just_above_normal(self):
        self.assertEqual(interpret_ph(7.46), "alkalemia")


class TestPCO2Interpretation(unittest.TestCase):
    """Test pCO2 classification."""

    def test_normal(self):
        self.assertEqual(interpret_pco2(40.0), "normal")

    def test_respiratory_acidosis(self):
        self.assertEqual(interpret_pco2(55.0), "respiratory acidosis")

    def test_respiratory_alkalosis(self):
        self.assertEqual(interpret_pco2(25.0), "respiratory alkalosis")

    def test_normal_low(self):
        self.assertEqual(interpret_pco2(35.0), "normal")

    def test_normal_high(self):
        self.assertEqual(interpret_pco2(45.0), "normal")


class TestHCO3Interpretation(unittest.TestCase):
    """Test bicarbonate classification."""

    def test_normal(self):
        self.assertEqual(interpret_hco3(24.0), "normal")

    def test_metabolic_acidosis(self):
        self.assertEqual(interpret_hco3(15.0), "metabolic acidosis")

    def test_metabolic_alkalosis(self):
        self.assertEqual(interpret_hco3(32.0), "metabolic alkalosis")

    def test_normal_low(self):
        self.assertEqual(interpret_hco3(22.0), "normal")

    def test_normal_high(self):
        self.assertEqual(interpret_hco3(26.0), "normal")


class TestAnionGap(unittest.TestCase):
    """Test anion gap calculation."""

    def test_normal_ag(self):
        """Na=140, Cl=104, HCO3=24 → AG = 140 - (104+24) = 12"""
        result = calculate_anion_gap(140, 104, 24)
        self.assertEqual(result["ag"], 12.0)
        self.assertFalse(result["is_elevated"])
        self.assertFalse(result["is_low"])

    def test_elevated_ag(self):
        """Na=148, Cl=100, HCO3=10 → AG = 148 - (100+10) = 38"""
        result = calculate_anion_gap(148, 100, 10)
        self.assertEqual(result["ag"], 38.0)
        self.assertTrue(result["is_elevated"])

    def test_low_ag(self):
        """Na=130, Cl=110, HCO3=26 → AG = 130 - (110+26) = -6"""
        result = calculate_anion_gap(130, 110, 26)
        self.assertEqual(result["ag"], -6.0)
        self.assertTrue(result["is_low"])

    def test_ag_with_potassium(self):
        """Na=140, K=4, Cl=104, HCO3=24 → AG = (140+4) - (104+24) = 16"""
        result = calculate_anion_gap(140, 104, 24, k=4.0)
        self.assertEqual(result["ag"], 16.0)
        # With K, normal range is 10-14, so 16 is elevated
        self.assertTrue(result["is_elevated"])

    def test_ag_boundary_normal(self):
        """AG exactly at upper normal boundary (12) should not be elevated."""
        result = calculate_anion_gap(140, 104, 24)
        self.assertEqual(result["ag"], 12.0)
        self.assertFalse(result["is_elevated"])


class TestWintersFormula(unittest.TestCase):
    """Test Winter's Formula: Expected pCO2 = 1.5 × HCO3 + 8 (±2)."""

    def test_basic_calculation(self):
        """HCO3=10 → expected pCO2 = 1.5×10 + 8 = 23"""
        result = winters_formula(10)
        self.assertEqual(result["expected_pco2"], 23.0)
        self.assertEqual(result["range_low"], 21.0)
        self.assertEqual(result["range_high"], 25.0)

    def test_hco3_15(self):
        """HCO3=15 → expected pCO2 = 1.5×15 + 8 = 30.5"""
        result = winters_formula(15)
        self.assertEqual(result["expected_pco2"], 30.5)

    def test_hco3_20(self):
        """HCO3=20 → expected pCO2 = 1.5×20 + 8 = 38"""
        result = winters_formula(20)
        self.assertEqual(result["expected_pco2"], 38.0)

    def test_assess_appropriate_compensation(self):
        """pCO2=23, HCO3=10 → expected 23, within range → appropriate."""
        result = assess_winters(23.0, 10.0)
        self.assertEqual(result["status"], "appropriate compensation")

    def test_assess_concurrent_respiratory_acidosis(self):
        """pCO2=30, HCO3=10 → expected 23 (range 21-25), actual 30 → too high."""
        result = assess_winters(30.0, 10.0)
        self.assertEqual(result["status"], "concurrent respiratory acidosis")
        self.assertGreater(result["deviation"], 0)

    def test_assess_concurrent_respiratory_alkalosis(self):
        """pCO2=18, HCO3=10 → expected 23 (range 21-25), actual 18 → too low."""
        result = assess_winters(18.0, 10.0)
        self.assertEqual(result["status"], "concurrent respiratory alkalosis")
        self.assertLess(result["deviation"], 0)


class TestDeltaRatio(unittest.TestCase):
    """Test delta-delta ratio calculation."""

    def test_pure_ag_metabolic_acidosis(self):
        """
        Na=148, Cl=100, HCO3=10
        AG = 148 - 100 - 10 = 38
        Delta AG = 38 - 12 = 26
        Delta HCO3 = 24 - 10 = 14
        Ratio = 26 / 14 = 1.86 → pure AG metabolic acidosis
        """
        ag = calculate_anion_gap(148, 100, 10)["ag"]
        result = calculate_delta_ratio(ag, 10)
        self.assertEqual(result["delta_ag"], 26.0)
        self.assertEqual(result["delta_hco3"], 14.0)
        self.assertAlmostEqual(result["delta_ratio"], 1.86, places=2)
        self.assertEqual(result["interpretation"], "pure anion gap metabolic acidosis")

    def test_mixed_ag_and_non_ag_acidosis(self):
        """
        Na=140, Cl=100, HCO3=10
        AG = 140 - 100 - 10 = 30
        Delta AG = 30 - 12 = 18
        Delta HCO3 = 24 - 10 = 14
        Ratio = 18 / 14 = 1.29 → pure AG metabolic acidosis
        (Let me pick values that give ratio < 1)
        Na=140, Cl=110, HCO3=10
        AG = 140 - 110 - 10 = 20
        Delta AG = 20 - 12 = 8
        Delta HCO3 = 24 - 10 = 14
        Ratio = 8 / 14 = 0.57 → mixed AG + non-AG
        """
        ag = calculate_anion_gap(140, 110, 10)["ag"]
        result = calculate_delta_ratio(ag, 10)
        self.assertEqual(result["delta_ag"], 8.0)
        self.assertAlmostEqual(result["delta_ratio"], 0.57, places=2)
        self.assertEqual(
            result["interpretation"],
            "mixed anion gap metabolic acidosis + non-anion gap metabolic acidosis"
        )

    def test_concurrent_metabolic_alkalosis(self):
        """
        Na=155, Cl=95, HCO3=15
        AG = 155 - 95 - 15 = 45
        Delta AG = 45 - 12 = 33
        Delta HCO3 = 24 - 15 = 9
        Ratio = 33 / 9 = 3.67 → concurrent metabolic alkalosis
        """
        ag = calculate_anion_gap(155, 95, 15)["ag"]
        result = calculate_delta_ratio(ag, 15)
        self.assertEqual(result["delta_ag"], 33.0)
        self.assertAlmostEqual(result["delta_ratio"], 3.67, places=2)
        self.assertEqual(result["interpretation"], "concurrent metabolic alkalosis")

    def test_no_change(self):
        """AG=12, HCO3=24 → delta_hco3=0, delta_ag=0 → no change."""
        result = calculate_delta_ratio(12.0, 24.0)
        self.assertIsNone(result["delta_ratio"])
        self.assertEqual(result["interpretation"], "no anion gap or bicarbonate change")


class TestRespiratoryAcidosisCompensation(unittest.TestCase):
    """Test compensation rules for respiratory acidosis."""

    def test_acute_compensation(self):
        """pCO2=60, expected acute HCO3 = 24 + 0.1×(60-40) = 26"""
        result = assess_compensation_respiratory_acidosis(60, 26)
        self.assertIn("acute", result["status"])
        self.assertEqual(result["acute_expected_hco3"], 26.0)

    def test_chronic_compensation(self):
        """pCO2=60, expected chronic HCO3 = 24 + 0.35×(60-40) = 31"""
        result = assess_compensation_respiratory_acidosis(60, 31)
        self.assertIn("chronic", result["status"])
        self.assertEqual(result["chronic_expected_hco3"], 31.0)

    def test_concurrent_metabolic_alkalosis(self):
        """pCO2=60, HCO3=40 → above chronic range → concurrent metabolic alkalosis."""
        result = assess_compensation_respiratory_acidosis(60, 40)
        self.assertIn("metabolic alkalosis", result["status"])

    def test_concurrent_metabolic_acidosis(self):
        """pCO2=60, HCO3=20 → below acute range → concurrent metabolic acidosis."""
        result = assess_compensation_respiratory_acidosis(60, 20)
        self.assertIn("metabolic acidosis", result["status"])


class TestRespiratoryAlkalosisCompensation(unittest.TestCase):
    """Test compensation rules for respiratory alkalosis."""

    def test_acute_compensation(self):
        """pCO2=25, expected acute HCO3 = 24 + 0.2×(25-40) = 21"""
        result = assess_compensation_respiratory_alkalosis(25, 21)
        self.assertIn("acute", result["status"])
        self.assertEqual(result["acute_expected_hco3"], 21.0)

    def test_chronic_compensation(self):
        """pCO2=25, expected chronic HCO3 = 24 + 0.5×(25-40) = 16.5"""
        result = assess_compensation_respiratory_alkalosis(25, 16.5)
        self.assertIn("chronic", result["status"])
        self.assertEqual(result["chronic_expected_hco3"], 16.5)


class TestMetabolicAlkalosisCompensation(unittest.TestCase):
    """Test compensation rules for metabolic alkalosis."""

    def test_appropriate_compensation(self):
        """HCO3=35, expected pCO2 = 0.7×35 + 20 = 44.5"""
        result = assess_compensation_metabolic_alkalosis(44.5, 35)
        self.assertIn("appropriate", result["status"])
        self.assertEqual(result["expected_pco2"], 44.5)

    def test_concurrent_respiratory_acidosis(self):
        """HCO3=35, expected ~44.5, actual pCO2=55 → too high."""
        result = assess_compensation_metabolic_alkalosis(55, 35)
        self.assertIn("respiratory acidosis", result["status"])


class TestFullABGInterpretation(unittest.TestCase):
    """Test complete ABG interpretation with known clinical scenarios."""

    def test_normal_abg(self):
        """Normal ABG: pH 7.40, pCO2 40, HCO3 24."""
        result = interpret_abg(7.40, 40.0, 24.0)
        self.assertEqual(result["ph_status"], "normal")
        self.assertEqual(result["primary_disorder"], "normal")
        self.assertEqual(result["compensation"]["type"], "none needed")

    def test_metabolic_acidosis_with_winters(self):
        """
        DKA patient: pH 7.25, pCO2 20, HCO3 10, Na 140, Cl 100.
        AG = 140 - 100 - 10 = 30 (elevated).
        Winter's expected pCO2 = 1.5×10 + 8 = 23 (range 21-25).
        Actual pCO2 = 20 → concurrent respiratory alkalosis.
        Delta AG = 18, Delta HCO3 = 14, Ratio = 1.29 → pure AG metabolic acidosis.
        """
        result = interpret_abg(7.25, 20.0, 10.0, na=140, cl=100)
        self.assertEqual(result["ph_status"], "acidemia")
        self.assertEqual(result["primary_disorder"], "metabolic acidosis")
        self.assertEqual(result["anion_gap"]["ag"], 30.0)
        self.assertTrue(result["anion_gap"]["is_elevated"])
        self.assertEqual(result["winters"]["expected_pco2"], 23.0)
        self.assertEqual(result["winters"]["status"], "concurrent respiratory alkalosis")
        self.assertAlmostEqual(result["delta_ratio"]["delta_ratio"], 1.29, places=2)

    def test_respiratory_acidosis_acute(self):
        """
        Acute respiratory failure: pH 7.28, pCO2 60, HCO3 26.
        Expected acute HCO3 = 24 + 0.1×20 = 26 → acute compensation.
        """
        result = interpret_abg(7.28, 60.0, 26.0)
        self.assertEqual(result["ph_status"], "acidemia")
        self.assertEqual(result["primary_disorder"], "respiratory acidosis")
        self.assertIn("acute", result["compensation"]["detail"])

    def test_respiratory_alkalosis(self):
        """
        Anxiety/hyperventilation: pH 7.52, pCO2 25, HCO3 21.
        Expected acute HCO3 = 24 + 0.2×(25-40) = 21 → acute compensation.
        """
        result = interpret_abg(7.52, 25.0, 21.0)
        self.assertEqual(result["ph_status"], "alkalemia")
        self.assertEqual(result["primary_disorder"], "respiratory alkalosis")
        self.assertIn("acute", result["compensation"]["detail"])

    def test_metabolic_alkalosis(self):
        """
        Vomiting: pH 7.52, pCO2 48, HCO3 38.
        Expected pCO2 = 0.7×38 + 20 = 46.6 (range 45.1-48.1).
        Actual 48 → appropriate compensation.
        """
        result = interpret_abg(7.52, 48.0, 38.0)
        self.assertEqual(result["ph_status"], "alkalemia")
        self.assertEqual(result["primary_disorder"], "metabolic alkalosis")
        self.assertIn("appropriate", result["compensation"]["detail"])

    def test_mixed_disorder_normal_ph(self):
        """
        Fully compensated respiratory acidosis with near-normal pH:
        pH 7.38, pCO2 50, HCO3 30.
        Elevated pCO2 (respiratory acidosis) with compensatory elevated HCO3.
        """
        result = interpret_abg(7.38, 50.0, 30.0)
        self.assertEqual(result["ph_status"], "normal")
        # This is fully compensated respiratory acidosis
        self.assertEqual(result["primary_disorder"], "fully compensated respiratory acidosis")

    def test_fully_compensated_respiratory_acidosis(self):
        """
        COPD patient: pH 7.37, pCO2 55, HCO3 32.
        pH is normal, pCO2 elevated, HCO3 elevated → fully compensated.
        """
        result = interpret_abg(7.37, 55.0, 32.0)
        self.assertEqual(result["ph_status"], "normal")
        self.assertEqual(result["primary_disorder"], "fully compensated respiratory acidosis")

    def test_interpret_row_from_csv(self):
        """Test CSV row interpretation."""
        row = {
            "pH": "7.25",
            "pco2": "20",
            "hco3": "10",
            "na": "140",
            "cl": "100",
        }
        result = interpret_row(row)
        self.assertEqual(result["primary_disorder"], "metabolic acidosis")
        self.assertEqual(result["anion_gap"]["ag"], 30.0)

    def test_interpret_row_missing_values(self):
        """Test CSV row with missing required values."""
        row = {"pH": "7.25"}
        result = interpret_row(row)
        self.assertIn("error", result)

    def test_severe_lactic_acidosis(self):
        """
        Septic shock: pH 7.10, pCO2 15, HCO3 5, Na 140, Cl 100.
        AG = 140 - 100 - 5 = 35 (very elevated).
        Winter's expected pCO2 = 1.5×5 + 8 = 15.5 (range 13.5-17.5).
        Actual pCO2 = 15 → appropriate compensation.
        Delta AG = 23, Delta HCO3 = 19, Ratio = 1.21 → pure AG metabolic acidosis.
        """
        result = interpret_abg(7.10, 15.0, 5.0, na=140, cl=100)
        self.assertEqual(result["primary_disorder"], "metabolic acidosis")
        self.assertEqual(result["anion_gap"]["ag"], 35.0)
        self.assertEqual(result["winters"]["status"], "appropriate compensation")
        self.assertAlmostEqual(result["delta_ratio"]["delta_ratio"], 1.21, places=2)

    def test_mixed_ag_and_non_ag_acidosis(self):
        """
        Diarrhea + lactic acidosis: pH 7.20, pCO2 18, HCO3 8, Na 140, Cl 110.
        AG = 140 - 110 - 8 = 22 (elevated).
        Winter's expected pCO2 = 1.5×8 + 8 = 20 (range 18-22).
        Actual pCO2 = 18 → at lower boundary, appropriate compensation.
        Delta AG = 10, Delta HCO3 = 16, Ratio = 0.625 → mixed AG + non-AG.
        """
        result = interpret_abg(7.20, 18.0, 8.0, na=140, cl=110)
        self.assertEqual(result["primary_disorder"], "metabolic acidosis")
        self.assertEqual(result["anion_gap"]["ag"], 22.0)
        self.assertAlmostEqual(result["delta_ratio"]["delta_ratio"], 0.62, places=2)
        self.assertIn("non-anion gap", result["delta_ratio"]["interpretation"])


if __name__ == "__main__":
    unittest.main()
