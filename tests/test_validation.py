"""
Tests for input validation and security features.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from abg_winter import (
    interpret_abg,
    assess_winters,
    process_csv,
    validate_ph,
    validate_pco2,
    validate_hco3,
    validate_na,
    validate_cl,
    validate_k,
    ABGValidationError,
)
from abg_disorders import MixedDisorderDetector, AnionGapDifferential


class TestInputValidation(unittest.TestCase):
    """Test clinical value range validation."""

    def test_valid_ph_values(self):
        """Valid pH values should not raise."""
        validate_ph(7.0)
        validate_ph(7.35)
        validate_ph(7.45)
        validate_ph(7.50)

    def test_invalid_ph_too_low(self):
        """pH below plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_ph(6.5)

    def test_invalid_ph_too_high(self):
        """pH above plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_ph(8.0)

    def test_invalid_ph_type(self):
        """Non-numeric pH should raise TypeError."""
        with self.assertRaises(TypeError):
            validate_ph("7.40")

    def test_valid_pco2_values(self):
        """Valid pCO2 values should not raise."""
        validate_pco2(40.0)
        validate_pco2(10.0)
        validate_pco2(100.0)

    def test_invalid_pco2(self):
        """pCO2 outside plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_pco2(200.0)
        with self.assertRaises(ABGValidationError):
            validate_pco2(1.0)

    def test_valid_hco3_values(self):
        """Valid HCO3 values should not raise."""
        validate_hco3(24.0)
        validate_hco3(5.0)
        validate_hco3(50.0)

    def test_invalid_hco3(self):
        """HCO3 outside plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_hco3(0.5)
        with self.assertRaises(ABGValidationError):
            validate_hco3(70.0)

    def test_valid_na_values(self):
        """Valid sodium values should not raise."""
        validate_na(140.0)
        validate_na(110.0)
        validate_na(160.0)

    def test_invalid_na(self):
        """Sodium outside plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_na(90.0)
        with self.assertRaises(ABGValidationError):
            validate_na(200.0)

    def test_valid_cl_values(self):
        """Valid chloride values should not raise."""
        validate_cl(100.0)
        validate_cl(70.0)
        validate_cl(130.0)

    def test_invalid_cl(self):
        """Chloride outside plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_cl(50.0)
        with self.assertRaises(ABGValidationError):
            validate_cl(150.0)

    def test_valid_k_values(self):
        """Valid potassium values should not raise."""
        validate_k(4.0)
        validate_k(1.5)
        validate_k(8.0)

    def test_invalid_k(self):
        """Potassium outside plausible range should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            validate_k(0.5)
        with self.assertRaises(ABGValidationError):
            validate_k(15.0)


class TestInterpretABGValidation(unittest.TestCase):
    """Test that interpret_abg validates inputs."""

    def test_valid_interpretation(self):
        """Valid ABG values should work normally."""
        result = interpret_abg(7.25, 20.0, 10.0, na=140.0, cl=100.0)
        self.assertEqual(result["primary_disorder"], "metabolic acidosis")

    def test_invalid_ph_raises(self):
        """Invalid pH should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(5.0, 40.0, 24.0)

    def test_invalid_pco2_raises(self):
        """Invalid pCO2 should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(7.40, 200.0, 24.0)

    def test_invalid_hco3_raises(self):
        """Invalid HCO3 should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(7.40, 40.0, 0.1)

    def test_invalid_na_raises(self):
        """Invalid Na should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(7.40, 40.0, 24.0, na=50.0, cl=100.0)

    def test_invalid_cl_raises(self):
        """Invalid Cl should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(7.40, 40.0, 24.0, na=140.0, cl=200.0)

    def test_invalid_k_raises(self):
        """Invalid K should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            interpret_abg(7.40, 40.0, 24.0, na=140.0, cl=100.0, k=20.0)


class TestAssessWintersValidation(unittest.TestCase):
    """Test that assess_winters validates inputs."""

    def test_valid_assessment(self):
        """Valid values should work normally."""
        result = assess_winters(23.0, 10.0)
        self.assertEqual(result["status"], "appropriate compensation")

    def test_invalid_pco2_raises(self):
        """Invalid pCO2 should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            assess_winters(200.0, 10.0)

    def test_invalid_hco3_raises(self):
        """Invalid HCO3 should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            assess_winters(40.0, 0.1)


class TestMixedDisorderDetectorValidation(unittest.TestCase):
    """Test that MixedDisorderDetector validates inputs."""

    def setUp(self):
        self.detector = MixedDisorderDetector()

    def test_valid_detection(self):
        """Valid values should work normally."""
        report = self.detector.detect(ph=7.25, pco2=20.0, hco3=10.0)
        self.assertIsNotNone(report.primary_disorder)

    def test_invalid_ph_raises(self):
        """Invalid pH should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            self.detector.detect(ph=5.0, pco2=40.0, hco3=24.0)

    def test_invalid_albumin_raises(self):
        """Invalid albumin should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            self.detector.detect(ph=7.40, pco2=40.0, hco3=24.0, albumin=10.0)


class TestAnionGapDifferentialValidation(unittest.TestCase):
    """Test that AnionGapDifferential validates inputs."""

    def setUp(self):
        self.diff = AnionGapDifferential()

    def test_valid_diagnosis(self):
        """Valid pH should work normally."""
        results = self.diff.diagnose(ag=25.0, ph=7.20)
        self.assertGreater(len(results), 0)

    def test_invalid_ph_raises(self):
        """Invalid pH should raise ABGValidationError."""
        with self.assertRaises(ABGValidationError):
            self.diff.diagnose(ag=25.0, ph=9.0)


class TestCSVSecurity(unittest.TestCase):
    """Test CSV processing security features."""

    def test_nonexistent_input_raises(self):
        """Non-existent input file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            process_csv("/nonexistent/path/input.csv", "/tmp/output.csv")

    def test_directory_as_input_raises(self):
        """Directory as input should raise ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                process_csv(tmpdir, os.path.join(tmpdir, "output.csv"))

    def test_nonexistent_output_dir_raises(self):
        """Non-existent output directory should raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "input.csv")
            with open(input_file, "w") as f:
                f.write("ph,pco2,hco3\n7.40,40,24\n")
            with self.assertRaises(FileNotFoundError):
                process_csv(input_file, "/nonexistent/dir/output.csv")

    def test_valid_csv_processing(self):
        """Valid CSV should process correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "input.csv")
            output_file = os.path.join(tmpdir, "output.csv")

            with open(input_file, "w", newline="") as f:
                f.write("ph,pco2,hco3,na,cl\n")
                f.write("7.40,40,24,140,104\n")
                f.write("7.25,20,10,140,100\n")

            results = process_csv(input_file, output_file)
            self.assertEqual(len(results), 2)
            self.assertTrue(os.path.exists(output_file))

    def test_path_traversal_protection(self):
        """Path traversal attempts should be resolved safely."""
        # This test verifies that paths with .. are resolved correctly
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, "input.csv")
            output_file = os.path.join(tmpdir, "output.csv")

            with open(input_file, "w", newline="") as f:
                f.write("ph,pco2,hco3\n7.40,40,24\n")

            # Use a path with .. components
            tricky_input = os.path.join(tmpdir, "subdir", "..", "input.csv")
            # Create subdir so the path exists
            os.makedirs(os.path.join(tmpdir, "subdir"), exist_ok=True)

            results = process_csv(tricky_input, output_file)
            self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
