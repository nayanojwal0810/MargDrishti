"""End-to-end data pipeline orchestrator for MargDrishti."""

import argparse
import sys
import time
from typing import Any, Dict, Optional

from marg_drishti.config import PipelineConfig
from marg_drishti.validation import DataValidator, ValidationReport
from marg_drishti.conversion import ParquetConverter
from marg_drishti.database import DatabaseManager


def run_data_pipeline(
    config: Optional[PipelineConfig] = None,
    convert_research: bool = True,
    overwrite_parquet: bool = True,
) -> Dict[str, Any]:
    """Execute complete ingestion, validation, Parquet conversion, and DuckDB mart creation."""
    config = config or PipelineConfig()
    config.ensure_directories()
    start_time = time.time()

    print("=" * 80)
    print("MARGDRISHTI: STARTING DATA FOUNDATION PIPELINE")
    print("=" * 80)
    print(f"Base Directory: {config.base_dir}")
    print(f"DuckDB Target : {config.duckdb_path}")

    # Step 1: Validation
    print("\n--- STEP 1: VALIDATING INPUT DATA ---")
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    print(report.summary_text())
    validator.close()

    if not report.is_valid:
        print("\n[ERROR] Raw data validation failed. Pipeline aborted.")
        return {
            "success": False,
            "validation_report": report,
            "error": "Validation failed",
        }

    # Step 2: Parquet Conversion
    print("\n--- STEP 2: CONVERTING CSV DATA TO PARQUET ---")
    converter = ParquetConverter(config)
    t0 = time.time()
    converted_files = converter.convert_all_official(overwrite=overwrite_parquet)
    for name, p in converted_files.items():
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"  Converted {name:<10} -> {p.name} ({size_mb:.2f} MB)")

    if convert_research and config.research_extracted_csv.exists():
        res_pq = converter.convert_research_dataset(overwrite=overwrite_parquet)
        if res_pq:
            res_mb = res_pq.stat().st_size / (1024 * 1024)
            print(f"  Converted research dataset -> {res_pq.name} ({res_mb:.2f} MB)")
    converter.close()
    print(f"Conversion completed in {time.time() - t0:.2f}s.")

    # Step 3: Database & Mart Build
    print("\n--- STEP 3: BUILDING DUCKDB TABLES & ANALYTICAL MARTS ---")
    db = DatabaseManager(config)
    t0 = time.time()
    row_counts = db.build_database()
    for tbl, count in row_counts.items():
        print(f"  Built {tbl:<28}: {count:,} rows")
    print(f"Database build completed in {time.time() - t0:.2f}s.")

    # Step 4: Integrity Verification
    print("\n--- STEP 4: VERIFYING JOIN AND GRAIN INTEGRITY ---")
    integrity = db.verify_integrity()
    db.close()

    print(f"  Staging Collisions: {integrity['stg_collisions_count']:,}")
    print(f"  Analytical Mart   : {integrity['mart_analytical_count']:,}")
    print(f"  Outcomes Mart     : {integrity['mart_outcomes_count']:,}")
    print(f"  Row Count Preserved: {'YES' if integrity['row_count_preserved'] else 'NO'}")
    print(f"  Duplicate Keys in Analytical Mart: {integrity['duplicate_mart_keys']}")
    print(f"  Duplicate Keys in Vehicle Summary: {integrity['duplicate_vehicle_summary_keys']}")

    total_time = time.time() - start_time
    success = integrity["is_valid"]

    print("\n" + "=" * 80)
    status_str = "SUCCESS" if success else "FAILED"
    print(f"PIPELINE EXECUTION {status_str} in {total_time:.2f}s")
    print("=" * 80)

    return {
        "success": success,
        "validation_report": report,
        "converted_files": converted_files,
        "row_counts": row_counts,
        "integrity": integrity,
        "total_time_seconds": total_time,
    }


def main():
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="MargDrishti Data Foundation Pipeline")
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Skip converting the 2020-2024 research archive dataset",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Do not overwrite existing Parquet files",
    )
    args = parser.parse_args()

    config = PipelineConfig()
    result = run_data_pipeline(
        config=config,
        convert_research=not args.skip_research,
        overwrite_parquet=not args.no_overwrite,
    )

    if not result["success"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
