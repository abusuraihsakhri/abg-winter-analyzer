#!/usr/bin/env python3
"""
CLI for ABG & Winter's Formula Analyzer.

Usage:
    python cli.py interpret --pH 7.25 --pco2 20 --hco3 10 --na 140 --cl 100
    python cli.py winters --hco3 10 --pco2 25
    python cli.py anion-gap --na 140 --cl 100 --hco3 10
    python cli.py delta-ratio --na 140 --cl 100 --hco3 10
    python cli.py batch --input sample.csv --output results.csv
"""
import argparse
import json
import sys

from abg_winter import (
    interpret_abg,
    winters_formula,
    assess_winters,
    calculate_anion_gap,
    calculate_delta_ratio,
    process_csv,
)


def cmd_interpret(args):
    """Full ABG interpretation."""
    result = interpret_abg(
        ph=args.ph,
        pco2=args.pco2,
        hco3=args.hco3,
        na=args.na,
        cl=args.cl,
        k=args.k,
    )
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        _print_interpretation(result)
    return 0


def cmd_winters(args):
    """Winter's Formula calculation."""
    if args.pco2 is not None:
        result = assess_winters(args.pco2, args.hco3)
    else:
        result = winters_formula(args.hco3)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 60)
        print("  WINTER'S FORMULA")
        print("=" * 60)
        print(f"  HCO3: {args.hco3} mEq/L")
        print(f"  Expected pCO2: {result['expected_pco2']} mmHg")
        print(f"  Acceptable range: {result['range_low']} - {result['range_high']} mmHg")
        if "actual_pco2" in result:
            print(f"  Actual pCO2: {result['actual_pco2']} mmHg")
            print(f"  Deviation: {result['deviation']} mmHg")
            print(f"  Assessment: {result['status']}")
            print(f"  {result['detail']}")
        print("=" * 60)
    return 0


def cmd_anion_gap(args):
    """Anion gap calculation."""
    result = calculate_anion_gap(args.na, args.cl, args.hco3, args.k)
    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 60)
        print("  ANION GAP")
        print("=" * 60)
        print(f"  Na: {args.na}  Cl: {args.cl}  HCO3: {args.hco3}")
        if args.k:
            print(f"  K: {args.k} (K-corrected formula)")
        print(f"  Anion Gap: {result['ag']} mEq/L")
        print(f"  Normal range: {result['normal_low']} - {result['normal_high']} mEq/L")
        if result["is_elevated"]:
            print("  Status: ELEVATED")
        elif result["is_low"]:
            print("  Status: LOW")
        else:
            print("  Status: NORMAL")
        print("=" * 60)
    return 0


def cmd_delta_ratio(args):
    """Delta-delta ratio calculation."""
    ag_result = calculate_anion_gap(args.na, args.cl, args.hco3, args.k)
    delta_result = calculate_delta_ratio(ag_result["ag"], args.hco3)
    if args.json:
        delta_result["anion_gap"] = ag_result
        print(json.dumps(delta_result, indent=2, default=str))
    else:
        print("=" * 60)
        print("  DELTA-DELTA RATIO")
        print("=" * 60)
        print(f"  Anion Gap: {ag_result['ag']} mEq/L")
        print(f"  Delta AG (AG - 12): {delta_result['delta_ag']}")
        print(f"  Delta HCO3 (24 - HCO3): {delta_result['delta_hco3']}")
        if delta_result["delta_ratio"] is not None:
            print(f"  Delta Ratio: {delta_result['delta_ratio']}")
        print(f"  Interpretation: {delta_result['interpretation']}")
        print("=" * 60)
    return 0


def cmd_batch(args):
    """Batch process a CSV file of ABG values."""
    results = process_csv(args.input, args.output)
    print(f"Processed {len(results)} records -> {args.output}")
    return 0


def _print_interpretation(result: dict):
    """Pretty-print a full ABG interpretation."""
    print("=" * 60)
    print("  ABG INTERPRETATION")
    print("=" * 60)
    print(f"  pH:    {result['ph']}   ({result['ph_status']})")
    print(f"  pCO2:  {result['pco2']} mmHg  ({result['pco2_status']})")
    print(f"  HCO3:  {result['hco3']} mEq/L  ({result['hco3_status']})")
    print()

    print(f"  Primary disorder: {result['primary_disorder']}")

    comp = result["compensation"]
    print(f"  Compensation: {comp['detail']}")
    if "expected_pco2" in comp:
        print(f"    Expected pCO2: {comp['expected_pco2']} mmHg (range {comp['range'][0]}-{comp['range'][1]})")
    if "acute_expected_hco3" in comp:
        print(f"    Acute expected HCO3: {comp['acute_expected_hco3']}")
        print(f"    Chronic expected HCO3: {comp['chronic_expected_hco3']}")

    if "anion_gap" in result:
        ag = result["anion_gap"]
        print()
        print(f"  Anion Gap: {ag['ag']} mEq/L (normal {ag['normal_low']}-{ag['normal_high']})")
        if ag["is_elevated"]:
            print("    ** ELEVATED **")

    if "delta_ratio" in result:
        dr = result["delta_ratio"]
        print(f"  Delta Ratio: {dr['delta_ratio']}")
        print(f"    {dr['interpretation']}")

    if "winters" in result:
        w = result["winters"]
        print()
        print(f"  Winter's Formula:")
        print(f"    Expected pCO2: {w['expected_pco2']} mmHg (range {w['range_low']}-{w['range_high']})")
        print(f"    Actual pCO2: {w['actual_pco2']} mmHg")
        print(f"    Deviation: {w['deviation']} mmHg")
        print(f"    Assessment: {w['status']}")

    print()
    print("  Summary:")
    print(f"    {result['clinical_summary']}")
    print("=" * 60)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="abg-winter-analyzer",
        description="ABG & Winter's Formula Analyzer — clinical acid-base interpretation",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- interpret ---
    p_interp = subparsers.add_parser(
        "interpret", help="Full ABG interpretation with anion gap and compensation"
    )
    p_interp.add_argument("--ph", type=float, required=True, help="Arterial pH")
    p_interp.add_argument("--pco2", type=float, required=True, help="pCO2 in mmHg")
    p_interp.add_argument("--hco3", type=float, required=True, help="HCO3 in mEq/L")
    p_interp.add_argument("--na", type=float, default=None, help="Sodium in mEq/L")
    p_interp.add_argument("--cl", type=float, default=None, help="Chloride in mEq/L")
    p_interp.add_argument("--k", type=float, default=None, help="Potassium in mEq/L")
    p_interp.add_argument("--json", action="store_true", help="Output as JSON")

    # --- winters ---
    p_winter = subparsers.add_parser(
        "winters", help="Winter's Formula: expected pCO2 for metabolic acidosis"
    )
    p_winter.add_argument("--hco3", type=float, required=True, help="HCO3 in mEq/L")
    p_winter.add_argument("--pco2", type=float, default=None, help="Actual pCO2 (optional, for assessment)")
    p_winter.add_argument("--json", action="store_true", help="Output as JSON")

    # --- anion-gap ---
    p_ag = subparsers.add_parser("anion-gap", help="Calculate anion gap")
    p_ag.add_argument("--na", type=float, required=True, help="Sodium in mEq/L")
    p_ag.add_argument("--cl", type=float, required=True, help="Chloride in mEq/L")
    p_ag.add_argument("--hco3", type=float, required=True, help="HCO3 in mEq/L")
    p_ag.add_argument("--k", type=float, default=None, help="Potassium in mEq/L (optional)")
    p_ag.add_argument("--json", action="store_true", help="Output as JSON")

    # --- delta-ratio ---
    p_dr = subparsers.add_parser("delta-ratio", help="Calculate delta-delta ratio")
    p_dr.add_argument("--na", type=float, required=True, help="Sodium in mEq/L")
    p_dr.add_argument("--cl", type=float, required=True, help="Chloride in mEq/L")
    p_dr.add_argument("--hco3", type=float, required=True, help="HCO3 in mEq/L")
    p_dr.add_argument("--k", type=float, default=None, help="Potassium in mEq/L (optional)")
    p_dr.add_argument("--json", action="store_true", help="Output as JSON")

    # --- batch ---
    p_batch = subparsers.add_parser("batch", help="Batch process ABG CSV file")
    p_batch.add_argument("--input", "-i", required=True, help="Input CSV path")
    p_batch.add_argument("--output", "-o", default="results.csv", help="Output CSV path")

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    commands = {
        "interpret": cmd_interpret,
        "winters": cmd_winters,
        "anion-gap": cmd_anion_gap,
        "delta-ratio": cmd_delta_ratio,
        "batch": cmd_batch,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
