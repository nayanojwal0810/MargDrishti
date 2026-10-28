"""Data validation and data quality profiling for MargDrishti.

Validates official DfT STATS19 CSV files, integrity constraints, and sentinel codes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import duckdb

from marg_drishti.config import (
    PipelineConfig,
    COLLISION_REQUIRED_COLUMNS,
    VEHICLE_REQUIRED_COLUMNS,
    CASUALTY_REQUIRED_COLUMNS,
    SENTINEL_UNKNOWN_CODE,
)


@dataclass
class ValidationReport:
    """Structured report detailing data validation and quality check outcomes."""

    is_valid: bool = True
    files_present: Dict[str, bool] = field(default_factory=dict)
    schemas_valid: Dict[str, bool] = field(default_factory=dict)
    missing_columns: Dict[str, List[str]] = field(default_factory=dict)
    row_counts: Dict[str, int] = field(default_factory=dict)
    blank_collision_ids: int = 0
    invalid_vehicle_keys: int = 0
    invalid_casualty_keys: int = 0
    duplicate_collision_ids: int = 0
    duplicate_vehicle_keys: int = 0
    duplicate_casualty_keys: int = 0
    orphaned_vehicles: int = 0
    orphaned_casualties: int = 0
    unlinked_vehicle_collisions: int = 0
    unlinked_casualty_collisions: int = 0
    collisions_with_vehicles_pct: float = 0.0
    collisions_with_casualties_pct: float = 0.0
    date_ranges: Dict[str, Tuple[str, str]] = field(default_factory=dict)
    severity_distribution: Dict[int, int] = field(default_factory=dict)
    missing_values: Dict[str, Dict[str, int]] = field(default_factory=dict)
    sentinel_unknown_values: Dict[str, Dict[str, int]] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary_text(self) -> str:
        """Render human-readable summary of validation results."""
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"=== DATA VALIDATION REPORT [{status}] ===",
            f"Official Files Checked: {len(self.files_present)} ({sum(self.files_present.values())} present)",
        ]
        for f, present in self.files_present.items():
            lines.append(f"  - {f}: {'PRESENT' if present else 'MISSING'}")

        lines.append("\nRow Counts:")
        for tbl, count in self.row_counts.items():
            lines.append(f"  - {tbl}: {count:,} rows")

        lines.append("\nIntegrity & Key Constraints:")
        lines.append(f"  - Missing or blank collision identifiers: {self.blank_collision_ids}")
        lines.append(f"  - Invalid or blank vehicle keys: {self.invalid_vehicle_keys}")
        lines.append(f"  - Invalid or blank casualty keys: {self.invalid_casualty_keys}")
        lines.append(f"  - Duplicate collision identifiers: {self.duplicate_collision_ids}")
        lines.append(f"  - Duplicate (collision, vehicle) keys: {self.duplicate_vehicle_keys}")
        lines.append(f"  - Duplicate (collision, casualty) keys: {self.duplicate_casualty_keys}")
        lines.append(f"  - Orphaned vehicle records: {self.orphaned_vehicles}")
        lines.append(f"  - Orphaned casualty records: {self.orphaned_casualties}")
        lines.append(f"  - Collisions linked to vehicle data: {self.collisions_with_vehicles_pct:.2f}% (unlinked: {self.unlinked_vehicle_collisions})")
        lines.append(f"  - Collisions linked to casualty data: {self.collisions_with_casualties_pct:.2f}% (unlinked: {self.unlinked_casualty_collisions})")

        if self.date_ranges:
            lines.append("\nTemporal Coverage:")
            for tbl, (min_d, max_d) in self.date_ranges.items():
                lines.append(f"  - {tbl}: {min_d} to {max_d}")

        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for err in self.errors:
                lines.append(f"  [ERROR] {err}")

        if self.warnings:
            lines.append(f"\nQuality Warnings / Informational Notes ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"  [WARN] {w}")

        return "\n".join(lines)


class DataValidator:
    """Performs schema, integrity, and quality checks on official STATS19 CSV data."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.con = duckdb.connect()

    def close(self):
        """Close internal DuckDB connection."""
        self.con.close()

    def check_file_existence(self) -> Dict[str, bool]:
        """Check presence of required official STATS19 CSV files."""
        return {
            "official_collision_csv": self.config.official_collision_csv.exists(),
            "official_vehicle_csv": self.config.official_vehicle_csv.exists(),
            "official_casualty_csv": self.config.official_casualty_csv.exists(),
        }

    def validate_csv_sources(self) -> ValidationReport:
        """Validate raw official CSV files and relational constraints."""
        report = ValidationReport()
        report.files_present = self.check_file_existence()

        # Check all three official files
        for key in ["official_collision_csv", "official_vehicle_csv", "official_casualty_csv"]:
            if not report.files_present.get(key, False):
                report.is_valid = False
                report.errors.append(f"Required raw file is missing: {key}")

        if not report.is_valid:
            return report

        coll_path = str(self.config.official_collision_csv).replace("\\", "/")
        veh_path = str(self.config.official_vehicle_csv).replace("\\", "/")
        cas_path = str(self.config.official_casualty_csv).replace("\\", "/")

        # 1. Schema check (fails gracefully if any required columns are missing)
        for name, path, required_cols in [
            ("collision", coll_path, COLLISION_REQUIRED_COLUMNS),
            ("vehicle", veh_path, VEHICLE_REQUIRED_COLUMNS),
            ("casualty", cas_path, CASUALTY_REQUIRED_COLUMNS),
        ]:
            cols_info = self.con.execute(f"DESCRIBE SELECT * FROM '{path}' LIMIT 1").fetchall()
            present_cols = set(c[0] for c in cols_info)
            missing = [c for c in required_cols if c not in present_cols]
            report.schemas_valid[name] = len(missing) == 0
            if missing:
                report.missing_columns[name] = missing
                report.is_valid = False
                report.errors.append(f"Table '{name}' missing required columns: {missing}")

        # Halt early if schema validation fails before running queries that depend on missing columns
        if not report.is_valid:
            return report

        # 2. Row counts
        report.row_counts["collision"] = self.con.execute(f"SELECT COUNT(*) FROM '{coll_path}'").fetchone()[0]
        report.row_counts["vehicle"] = self.con.execute(f"SELECT COUNT(*) FROM '{veh_path}'").fetchone()[0]
        report.row_counts["casualty"] = self.con.execute(f"SELECT COUNT(*) FROM '{cas_path}'").fetchone()[0]

        # 3. Collision identifier presence and non-blank check
        blank_coll_ids = self.con.execute(f"""
            SELECT COUNT(*) FROM '{coll_path}'
            WHERE collision_index IS NULL OR TRIM(CAST(collision_index AS VARCHAR)) = ''
        """).fetchone()[0]
        report.blank_collision_ids = blank_coll_ids
        if blank_coll_ids > 0:
            report.is_valid = False
            report.errors.append(f"Found {blank_coll_ids} missing or blank collision_index records in collision table.")

        # 4. Collision identifier primary key uniqueness
        dup_count = self.con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM '{coll_path}'
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        report.duplicate_collision_ids = dup_count
        if dup_count > 0:
            report.is_valid = False
            report.errors.append(f"Found {dup_count} duplicate collision_index records in collision table.")

        # 5. Vehicle key presence and non-blank check
        invalid_veh_keys = self.con.execute(f"""
            SELECT COUNT(*) FROM '{veh_path}'
            WHERE collision_index IS NULL OR TRIM(CAST(collision_index AS VARCHAR)) = ''
               OR vehicle_reference IS NULL OR TRIM(CAST(vehicle_reference AS VARCHAR)) = ''
        """).fetchone()[0]
        report.invalid_vehicle_keys = invalid_veh_keys
        if invalid_veh_keys > 0:
            report.is_valid = False
            report.errors.append(f"Found {invalid_veh_keys} invalid or blank key records (collision_index or vehicle_reference) in vehicle table.")

        # 6. Composite child key uniqueness in vehicle data: (collision_index, vehicle_reference)
        dup_veh_keys = self.con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT collision_index, vehicle_reference FROM '{veh_path}'
                GROUP BY collision_index, vehicle_reference HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        report.duplicate_vehicle_keys = dup_veh_keys
        if dup_veh_keys > 0:
            report.is_valid = False
            report.errors.append(f"Found {dup_veh_keys} duplicate (collision_index, vehicle_reference) keys in vehicle table.")

        # 7. Casualty key presence and non-blank check
        invalid_cas_keys = self.con.execute(f"""
            SELECT COUNT(*) FROM '{cas_path}'
            WHERE collision_index IS NULL OR TRIM(CAST(collision_index AS VARCHAR)) = ''
               OR casualty_reference IS NULL OR TRIM(CAST(casualty_reference AS VARCHAR)) = ''
        """).fetchone()[0]
        report.invalid_casualty_keys = invalid_cas_keys
        if invalid_cas_keys > 0:
            report.is_valid = False
            report.errors.append(f"Found {invalid_cas_keys} invalid or blank key records (collision_index or casualty_reference) in casualty table.")

        # 8. Composite child key uniqueness in casualty data: (collision_index, casualty_reference)
        dup_cas_keys = self.con.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT collision_index, casualty_reference FROM '{cas_path}'
                GROUP BY collision_index, casualty_reference HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        report.duplicate_casualty_keys = dup_cas_keys
        if dup_cas_keys > 0:
            report.is_valid = False
            report.errors.append(f"Found {dup_cas_keys} duplicate (collision_index, casualty_reference) keys in casualty table.")

        # 9. Foreign key integrity: vehicle -> collision
        orphaned_veh = self.con.execute(f"""
            SELECT COUNT(*) FROM '{veh_path}' v
            LEFT JOIN '{coll_path}' c ON CAST(v.collision_index AS VARCHAR) = CAST(c.collision_index AS VARCHAR)
            WHERE c.collision_index IS NULL
        """).fetchone()[0]
        report.orphaned_vehicles = orphaned_veh
        if orphaned_veh > 0:
            report.is_valid = False
            report.errors.append(f"Found {orphaned_veh} orphaned vehicle records that do not link to any collision.")

        # 10. Foreign key integrity: casualty -> collision
        orphaned_cas = self.con.execute(f"""
            SELECT COUNT(*) FROM '{cas_path}' k
            LEFT JOIN '{coll_path}' c ON CAST(k.collision_index AS VARCHAR) = CAST(c.collision_index AS VARCHAR)
            WHERE c.collision_index IS NULL
        """).fetchone()[0]
        report.orphaned_casualties = orphaned_cas
        if orphaned_cas > 0:
            report.is_valid = False
            report.errors.append(f"Found {orphaned_cas} orphaned casualty records that do not link to any collision.")

        # 11. Child record coverage: every collision must have linked vehicle and casualty records
        total_coll = report.row_counts["collision"]
        if total_coll > 0:
            matched_veh = self.con.execute(f"""
                SELECT COUNT(DISTINCT c.collision_index)
                FROM '{coll_path}' c
                JOIN '{veh_path}' v ON CAST(c.collision_index AS VARCHAR) = CAST(v.collision_index AS VARCHAR)
            """).fetchone()[0]
            matched_cas = self.con.execute(f"""
                SELECT COUNT(DISTINCT c.collision_index)
                FROM '{coll_path}' c
                JOIN '{cas_path}' k ON CAST(c.collision_index AS VARCHAR) = CAST(k.collision_index AS VARCHAR)
            """).fetchone()[0]
            report.collisions_with_vehicles_pct = (matched_veh / total_coll) * 100.0
            report.collisions_with_casualties_pct = (matched_cas / total_coll) * 100.0

            unlinked_veh = total_coll - matched_veh
            report.unlinked_vehicle_collisions = unlinked_veh
            if unlinked_veh > 0:
                report.is_valid = False
                report.errors.append(
                    f"{unlinked_veh} collision records have no linked vehicle records ({report.collisions_with_vehicles_pct:.2f}% coverage). Complete vehicle coverage is required."
                )

            unlinked_cas = total_coll - matched_cas
            report.unlinked_casualty_collisions = unlinked_cas
            if unlinked_cas > 0:
                report.is_valid = False
                report.errors.append(
                    f"{unlinked_cas} collision records have no linked casualty records ({report.collisions_with_casualties_pct:.2f}% coverage). Complete casualty coverage is required."
                )

        # 12. Date range check
        date_stats = self.con.execute(f"SELECT MIN(date), MAX(date) FROM '{coll_path}'").fetchone()
        report.date_ranges["collision"] = (str(date_stats[0]), str(date_stats[1]))

        # 13. Collision severity distribution
        sev_counts = self.con.execute(f"""
            SELECT collision_severity, COUNT(*)
            FROM '{coll_path}'
            GROUP BY collision_severity
            ORDER BY collision_severity
        """).fetchall()
        report.severity_distribution = {row[0]: row[1] for row in sev_counts}

        # 14. Check missing & sentinel -1 values across key collision features
        check_cols = [
            "speed_limit", "road_type", "light_conditions",
            "weather_conditions", "road_surface_conditions",
            "junction_control", "local_authority_district",
            "local_authority_ons_district"
        ]
        report.missing_values["collision"] = {}
        report.sentinel_unknown_values["collision"] = {}

        for col in check_cols:
            null_count = self.con.execute(f"SELECT COUNT(*) FROM '{coll_path}' WHERE {col} IS NULL").fetchone()[0]
            neg1_count = self.con.execute(f"SELECT COUNT(*) FROM '{coll_path}' WHERE CAST({col} AS VARCHAR) IN ('-1', '-1.0')").fetchone()[0]
            report.missing_values["collision"][col] = null_count
            report.sentinel_unknown_values["collision"][col] = neg1_count
            if neg1_count > 0:
                report.warnings.append(
                    f"Column '{col}' has {neg1_count:,} records coded as -1 (Data missing / Unknown)."
                )

        return report
