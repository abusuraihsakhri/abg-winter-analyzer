"""
Tests for mixed disorder detection and anion gap differential diagnosis (abg_disorders.py).
"""
import unittest
from abg_disorders import (
    MixedDisorderDetector,
    AnionGapDifferential,
    AcidBaseDisorder,
    MixedDisorderReport,
)


class TestMixedDisorderDetector(unittest.TestCase):
    def setUp(self):
        self.detector = MixedDisorderDetector()

    def test_metabolic_acidosis_detection(self):
        """Test DKA metabolic acidosis detection."""
        report = self.detector.detect(ph=7.25, pco2=20.0, hco3=10.0, na=140.0, cl=100.0)
        self.assertIsInstance(report, MixedDisorderReport)
        self.assertEqual(report.anion_gap, 30.0)
        self.assertEqual(report.primary_disorder, "Metabolic acidosis")
        self.assertTrue(len(report.disorders) > 0)
        self.assertIn("Metabolic acidosis", report.narrative)

    def test_respiratory_acidosis_detection(self):
        """Test respiratory acidosis detection."""
        report = self.detector.detect(ph=7.28, pco2=60.0, hco3=26.0)
        self.assertEqual(report.primary_disorder, "Respiratory acidosis")
        self.assertTrue(any(d.name == "Respiratory acidosis" for d in report.disorders))

    def test_metabolic_alkalosis_detection(self):
        """Test metabolic alkalosis detection."""
        report = self.detector.detect(ph=7.52, pco2=48.0, hco3=38.0)
        self.assertEqual(report.primary_disorder, "Metabolic alkalosis")

    def test_respiratory_alkalosis_detection(self):
        """Test respiratory alkalosis detection."""
        report = self.detector.detect(ph=7.52, pco2=25.0, hco3=21.0)
        self.assertEqual(report.primary_disorder, "Respiratory alkalosis")

    def test_normal_ph_compensated_respiratory_acidosis(self):
        """Test compensated respiratory acidosis with normal pH."""
        report = self.detector.detect(ph=7.38, pco2=50.0, hco3=30.0)
        self.assertIn("Fully compensated respiratory acidosis", report.narrative)

    def test_normal_ph_compensated_respiratory_alkalosis(self):
        """Test compensated respiratory alkalosis with normal pH."""
        report = self.detector.detect(ph=7.42, pco2=28.0, hco3=18.0)
        self.assertIn("Fully compensated respiratory alkalosis", report.narrative)

    def test_normal_ph_pure_normal(self):
        """Test completely normal ABG."""
        report = self.detector.detect(ph=7.40, pco2=40.0, hco3=24.0)
        self.assertEqual(len(report.disorders), 0)
        self.assertIn("No acute acid-base disorder detected", report.narrative)

    def test_albumin_correction_for_anion_gap(self):
        """Test anion gap adjustment when hypoalbuminemia is present."""
        # Albumin 2.0 (normal 4.0 or baseline 3.5 in formula)
        report_normal_alb = self.detector.detect(ph=7.30, pco2=30.0, hco3=15.0, na=140.0, cl=100.0, albumin=4.0)
        report_low_alb = self.detector.detect(ph=7.30, pco2=30.0, hco3=15.0, na=140.0, cl=100.0, albumin=2.0)
        self.assertNotEqual(report_normal_alb.anion_gap, report_low_alb.anion_gap)


class TestAnionGapDifferential(unittest.TestCase):
    def setUp(self):
        self.diff = AnionGapDifferential()

    def test_normal_anion_gap(self):
        """Normal AG should return normal status."""
        results = self.diff.diagnose(ag=10.0)
        self.assertEqual(len(results), 1)
        self.assertIn("Normal anion gap", results[0]["cause"])

    def test_elevated_anion_gap_with_high_lactate(self):
        """High lactate should prioritize lactic acidosis."""
        results = self.diff.diagnose(ag=25.0, ph=7.20, lactate=6.5)
        self.assertGreater(len(results), 1)
        self.assertEqual(results[0]["cause"], "Lactic acidosis")

    def test_elevated_anion_gap_with_high_glucose(self):
        """High glucose should prioritize DKA."""
        results = self.diff.diagnose(ag=28.0, ph=7.18, glucose=450.0)
        self.assertGreater(len(results), 1)
        self.assertEqual(results[0]["cause"], "Diabetic ketoacidosis")

    def test_elevated_anion_gap_with_high_bun(self):
        """High BUN should prioritize Uremia."""
        results = self.diff.diagnose(ag=22.0, ph=7.25, bun=85.0)
        self.assertGreater(len(results), 1)
        self.assertEqual(results[0]["cause"], "Uremia")


if __name__ == "__main__":
    unittest.main()
