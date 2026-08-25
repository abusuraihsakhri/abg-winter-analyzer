"""
Tests for ABG & Winter's Formula Analyzer — CLI integration.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from cli import main


def test_cli_interpret_basic(capsys):
    """Test CLI interpret command with basic ABG values."""
    ret = main(["interpret", "--pH", "7.25", "--pco2", "20", "--hco3", "10",
                "--na", "140", "--cl", "100"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "metabolic acidosis" in captured.out
    assert "Anion Gap" in captured.out


def test_cli_interpret_json(capsys):
    """Test CLI interpret command with JSON output."""
    ret = main(["interpret", "--pH", "7.40", "--pco2", "40", "--hco3", "24", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert '"primary_disorder"' in captured.out
    assert '"normal"' in captured.out


def test_cli_winters(capsys):
    """Test CLI winters command."""
    ret = main(["winters", "--hco3", "10"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "23.0" in captured.out  # 1.5*10+8 = 23


def test_cli_winters_with_pco2(capsys):
    """Test CLI winters command with actual pCO2 assessment."""
    ret = main(["winters", "--hco3", "10", "--pco2", "30"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "respiratory acidosis" in captured.out


def test_cli_anion_gap(capsys):
    """Test CLI anion-gap command."""
    ret = main(["anion-gap", "--na", "140", "--cl", "100", "--hco3", "10"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "30.0" in captured.out  # 140 - 100 - 10 = 30
    assert "ELEVATED" in captured.out


def test_cli_delta_ratio(capsys):
    """Test CLI delta-ratio command."""
    ret = main(["delta-ratio", "--na", "140", "--cl", "100", "--hco3", "10"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Delta Ratio" in captured.out


def test_cli_batch(tmp_path):
    """Test CLI batch command with a CSV file."""
    import csv
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"

    with open(input_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["pH", "pco2", "hco3", "na", "cl"])
        writer.writerow([7.25, 20, 10, 140, 100])
        writer.writerow([7.40, 40, 24, 140, 104])

    ret = main(["batch", "--input", str(input_file), "--output", str(output_file)])
    assert ret == 0
    assert output_file.exists()

    with open(output_file, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert "primary_disorder" in rows[0]
