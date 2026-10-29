#!/usr/bin/env python
"""MargDrishti Severity Benchmarking Entrypoint.

Usage:
    python run_benchmark.py
"""

import json
import sys
from pathlib import Path

# Add src to python path for direct execution
sys.path.insert(0, str(Path(__file__).parent / "src"))

import duckdb
from marg_drishti.benchmarking import run_severity_benchmark
from marg_drishti.config import PipelineConfig


def main() -> None:
    config = PipelineConfig()
    db_path = config.duckdb_path

    # 1. Check database exists (do not create an empty database)
    if not db_path.exists():
        print(f"Error: Processed database not found at '{db_path}'.", file=sys.stderr)
        print("Please run 'python run_pipeline.py' first to build the pipeline.", file=sys.stderr)
        sys.exit(1)

    # 2. Connect read-only and verify mart_collision_analytical exists
    try:
        con = duckdb.connect(str(db_path), read_only=True)
    except Exception as exc:
        print(f"Error opening database '{db_path}': {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        if "mart_collision_analytical" not in tables:
            print(
                "Error: Analytical mart 'mart_collision_analytical' not found in database.",
                file=sys.stderr,
            )
            print("Please run 'python run_pipeline.py' first to build data marts.", file=sys.stderr)
            sys.exit(1)

        print("Reading 'mart_collision_analytical' from database...")
        df = con.execute("SELECT * FROM mart_collision_analytical").df()
    finally:
        con.close()

    print(f"Loaded {len(df):,} total collision records.")

    # 3. Fit cross-validated baseline model and calculate authority benchmark
    print("Fitting stratified cross-validated baseline logistic regression...")
    benchmark_df, summary, _ = run_severity_benchmark(df)

    # 4. Save results to data/processed/benchmarks/
    output_dir = config.processed_dir / "benchmarks"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "area_severity_benchmark.csv"
    json_path = output_dir / "area_severity_benchmark_summary.json"

    benchmark_df.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # 5. Print concise console summary
    rec = summary["record_counts"]
    metrics = summary["overall_metrics"]
    settings = summary["model_settings"]

    print("\n" + "=" * 80)
    print("MargDrishti: Case-Mix-Adjusted KSI Severity Benchmarking")
    print("=" * 80)
    print(f"Model: {settings['model_type']} (L2 Regularization, Solver: {settings['solver']})")
    print(f"Encoding: {settings['encoding']}")
    print(f"Random Seed: {settings['random_seed']} | Stratified Folds: {settings['folds_used']}")
    print("-" * 80)
    print("Cohort & Eligibility Summary:")
    print(f"  Total Collision Records:                 {rec['total_collision_records']:>10,}")
    print(f"  Eligible Collisions (Known Severity):    {rec['eligible_collision_count']:>10,}")
    print(f"  Excluded (Missing/Invalid Severity):     {rec['missing_or_invalid_severity_count']:>10,}")
    print(f"  Records with Missing/Invalid Authority:  {rec['invalid_or_missing_authority_count']:>10,}")
    print(f"  Highway Authorities Benchmarked:         {rec['authorities_benchmarked_count']:>10,}")
    print("-" * 80)
    print("Overall Severity Baseline (Known Severity across Benchmarked Authorities):")
    print(f"  Known-Severity Collisions:               {metrics['overall_known_severity_collision_count']:>10,}")
    print(f"  Observed KSI Collisions:                 {metrics['overall_observed_ksi_count']:>10,}")
    if metrics["overall_observed_ksi_share_pct"] is not None:
        print(f"  Observed KSI Share:                      {metrics['overall_observed_ksi_share_pct']:>9.2f}%")
    if metrics["overall_expected_ksi_count"] is not None:
        print(f"  Expected KSI Collisions:                 {metrics['overall_expected_ksi_count']:>10,.2f}")
    if metrics["overall_expected_ksi_share_pct"] is not None:
        print(f"  Expected KSI Share:                      {metrics['overall_expected_ksi_share_pct']:>9.2f}%")
    print("-" * 80)
    print("Output Files Generated:")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    print("=" * 80)
    print("Interpretation & Governance:")
    print("  Index 100 = Observed KSI matches expected KSI for fitted case mix.")
    print("  Index > 100 = Higher observed KSI than expected; Index < 100 = Lower.")
    print("  Note: Observational analysis of police-reported personal-injury collisions.")
    print("        Not an exposure-adjusted collision risk or causal safety assessment.")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
