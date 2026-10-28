# Data Pipeline Guide

This document describes the design, execution, and configuration of the MargDrishti data pipeline.

---

## 1. Pipeline Architecture

The pipeline consists of four sequential stages:

```
[1. Validation]  ──►  [2. Parquet Conversion]  ──►  [3. Database Build]  ──►  [4. Integrity Verification]
 Check schema,         Convert CSVs to              Execute SQL DDL           Assert row counts,
 duplicates,           compressed Parquet           and transformations        unique grains,
 foreign keys.         via DuckDB COPY.             in DuckDB.                 and no join fan-out.
```

### Key Principles
- **No silent value alteration:** Missing data and `-1` sentinel codes are identified and documented, not silently set to zero.
- **Relational grain preservation:** Vehicle and casualty tables are aggregated to the collision grain before joining, ensuring collisions are never duplicated.
- **Outcome separation:** Post-crash casualty outcomes are isolated from pre-crash analytical mart features.
- **Raw data immutability:** The pipeline treats raw data as read-only. Source files are never modified or rewritten.

---

## 2. Requirements & Environment Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Core libraries:
- `duckdb>=1.0.0`: Embedded columnar SQL analytics engine.
- `pyarrow>=14.0.0`: Apache Parquet reading and writing.
- `pandas>=2.0.0`: Tabular data processing.
- `pytest>=8.0.0`: Automated test framework.

---

## 3. Running the Pipeline

Execute the pipeline from the project root:

```bash
python run_pipeline.py
```

Optional CLI flags:
- `--skip-research`: Skip conversion of the research dataset archive (`UKdata.csv`).
- `--no-overwrite`: Skip regenerating Parquet files if they already exist.

Expected Output Summary:
```
================================================================================
MARGDRISHTI: STARTING DATA FOUNDATION PIPELINE
================================================================================
--- STEP 1: VALIDATING INPUT DATA ---
=== DATA VALIDATION REPORT [PASSED] ===
Files Checked: 5 (5 present)
Row Counts:
  - collision: 513,801 rows
  - vehicle: 937,265 rows
  - casualty: 652,821 rows
Integrity & Key Constraints:
  - Duplicate collision identifiers: 0
  - Orphaned vehicle records: 0
  - Orphaned casualty records: 0
  - Collisions linked to vehicle data: 100.00%
  - Collisions linked to casualty data: 100.00%

--- STEP 2: CONVERTING CSV DATA TO PARQUET ---
  Converted collision  -> official_collision_2021_2025.parquet (30.72 MB)
  Converted vehicle    -> official_vehicle_2021_2025.parquet (26.69 MB)
  Converted casualty   -> official_casualty_2021_2025.parquet (16.99 MB)

--- STEP 3: BUILDING DUCKDB TABLES & ANALYTICAL MARTS ---
  Built raw_collisions              : 513,801 rows
  Built raw_vehicles                : 937,265 rows
  Built raw_casualties              : 652,821 rows
  Built stg_collisions              : 513,801 rows
  Built agg_vehicle_summary         : 513,801 rows
  Built agg_casualty_summary        : 513,801 rows
  Built mart_collision_analytical   : 513,801 rows
  Built mart_collision_outcomes     : 513,801 rows

--- STEP 4: VERIFYING JOIN AND GRAIN INTEGRITY ---
  Staging Collisions: 513,801
  Analytical Mart   : 513,801
  Outcomes Mart     : 513,801
  Row Count Preserved: YES
  Duplicate Keys in Analytical Mart: 0
  Duplicate Keys in Vehicle Summary: 0
================================================================================
PIPELINE EXECUTION SUCCESS
================================================================================
```

---

## 4. Running Automated Tests

Run the automated test suite:

```bash
pytest
```

The test suite covers:
- Source schema validation and missing column detection (`tests/test_validation.py`).
- Primary key uniqueness and duplicate identifier detection (`tests/test_validation.py`).
- Foreign key integrity and orphaned record detection (`tests/test_validation.py`).
- CSV to Parquet conversion fidelity (`tests/test_conversion.py`).
- Row count preservation and join fan-out prevention (`tests/test_database.py`).
- Vehicle summary aggregation correctness at collision grain (`tests/test_database.py`).
- Separation of casualty outcomes from the analytical mart (`tests/test_database.py`).
- Raw data file immutability across pipeline execution (`tests/test_pipeline.py`).
