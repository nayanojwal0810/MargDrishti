"""DuckDB database initialization and analytical mart build manager for MargDrishti."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import duckdb

from marg_drishti.config import PipelineConfig


class DatabaseManager:
    """Manages DuckDB connection, SQL execution, table builds, and data integrity checks."""

    def __init__(self, config: Optional[PipelineConfig] = None, database_path: Optional[Path] = None):
        self.config = config or PipelineConfig()
        self.db_path = database_path or self.config.duckdb_path
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.con = duckdb.connect(str(self.db_path))
        else:
            self.con = duckdb.connect(":memory:")

    def close(self):
        """Close connection."""
        self.con.close()

    def execute_script(self, script_path: Path, substitutions: Optional[Dict[str, str]] = None) -> None:
        """Read and execute a SQL file, applying string substitutions."""
        if not script_path.exists():
            raise FileNotFoundError(f"SQL file not found: {script_path}")

        sql_text = script_path.read_text(encoding="utf-8")
        if substitutions:
            for k, v in substitutions.items():
                sql_text = sql_text.replace(f"{{{k}}}", v.replace("\\", "/"))

        self.con.execute(sql_text)

    def build_database(self) -> Dict[str, int]:
        """Execute all SQL transformations in dependency order and return table row counts."""
        parquet_dir_str = str(self.config.parquet_dir).replace("\\", "/")
        substitutions = {"parquet_dir": parquet_dir_str}

        sql_files = [
            "01_raw_views.sql",
            "02_stg_collisions.sql",
            "03_agg_vehicle_summary.sql",
            "04_agg_casualty_summary.sql",
            "05_marts.sql",
        ]

        for sql_file in sql_files:
            file_path = self.config.sql_dir / sql_file
            self.execute_script(file_path, substitutions=substitutions)

        # Gather row counts for all official tables and marts
        tables_to_check = [
            "raw_collisions",
            "raw_vehicles",
            "raw_casualties",
            "stg_collisions",
            "agg_vehicle_summary",
            "agg_casualty_summary",
            "mart_collision_analytical",
            "mart_collision_outcomes",
        ]
        counts = {}
        for tbl in tables_to_check:
            counts[tbl] = self.con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

        return counts

    def verify_integrity(self) -> Dict[str, Any]:
        """Execute comprehensive integrity and constraint checks across all marts."""
        stg_count = self.con.execute("SELECT COUNT(*) FROM stg_collisions").fetchone()[0]
        mart_count = self.con.execute("SELECT COUNT(*) FROM mart_collision_analytical").fetchone()[0]
        outcomes_count = self.con.execute("SELECT COUNT(*) FROM mart_collision_outcomes").fetchone()[0]

        # 1. Uniqueness of collision_index across all marts
        dup_stg = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM stg_collisions
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        dup_mart = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM mart_collision_analytical
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        dup_outcomes = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM mart_collision_outcomes
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        dup_veh_summary = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM agg_vehicle_summary
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        dup_cas_summary = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM agg_casualty_summary
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        # 2. Foreign-key link verification (summaries -> collisions)
        orphaned_veh_summary = self.con.execute("""
            SELECT COUNT(*) FROM agg_vehicle_summary v
            LEFT JOIN stg_collisions c ON v.collision_index = c.collision_index
            WHERE c.collision_index IS NULL
        """).fetchone()[0]

        orphaned_cas_summary = self.con.execute("""
            SELECT COUNT(*) FROM agg_casualty_summary k
            LEFT JOIN stg_collisions c ON k.collision_index = c.collision_index
            WHERE c.collision_index IS NULL
        """).fetchone()[0]

        # 3. Severity label and binary target consistency
        inconsistent_severities = self.con.execute("""
            SELECT COUNT(*) FROM stg_collisions
            WHERE (collision_severity = 1 AND (is_fatal_or_serious != 1 OR collision_severity_name != 'Fatal'))
               OR (collision_severity = 2 AND (is_fatal_or_serious != 1 OR collision_severity_name != 'Serious'))
               OR (collision_severity = 3 AND (is_fatal_or_serious != 0 OR collision_severity_name != 'Slight'))
               OR (collision_severity NOT IN (1, 2, 3) AND (is_fatal_or_serious IS NOT NULL OR collision_severity_name IS NOT NULL))
        """).fetchone()[0]

        # 4. Strict exclusion of casualty outcomes from the analytical mart
        analytical_cols = [
            c[0].lower() for c in self.con.execute("DESCRIBE SELECT * FROM mart_collision_analytical").fetchall()
        ]
        forbidden_outcome_cols = [
            "fatal_casualty_count",
            "serious_casualty_count",
            "slight_casualty_count",
            "ksi_casualty_count",
            "has_fatal_casualty",
            "has_ksi_casualty",
            "pedestrian_casualty_count",
            "cyclist_casualty_count",
            "motorcyclist_casualty_count",
            "driver_casualty_count",
            "passenger_casualty_count",
            "child_casualty_count",
            "elderly_casualty_count",
            "youngest_casualty_age",
            "oldest_casualty_age",
        ]
        leaked_outcomes = [col for col in forbidden_outcome_cols if col in analytical_cols]

        # 5. Missing time handling check (no midnight substitution)
        midnight_substitutions = self.con.execute("""
            SELECT COUNT(*) FROM stg_collisions
            WHERE collision_time IS NULL
              AND collision_timestamp IS NOT NULL
        """).fetchone()[0]

        # 6. Overall validation status
        row_count_preserved = (stg_count == mart_count == outcomes_count)
        all_unique = (dup_stg == 0 and dup_mart == 0 and dup_outcomes == 0 and dup_veh_summary == 0 and dup_cas_summary == 0)
        no_orphans = (orphaned_veh_summary == 0 and orphaned_cas_summary == 0)
        severity_consistent = (inconsistent_severities == 0)
        no_leaks = (len(leaked_outcomes) == 0)
        times_clean = (midnight_substitutions == 0)

        is_valid = (
            row_count_preserved
            and all_unique
            and no_orphans
            and severity_consistent
            and no_leaks
            and times_clean
        )

        return {
            "stg_collisions_count": stg_count,
            "mart_analytical_count": mart_count,
            "mart_outcomes_count": outcomes_count,
            "row_count_preserved": row_count_preserved,
            "duplicate_stg_keys": dup_stg,
            "duplicate_mart_keys": dup_mart,
            "duplicate_outcomes_keys": dup_outcomes,
            "duplicate_vehicle_summary_keys": dup_veh_summary,
            "duplicate_casualty_summary_keys": dup_cas_summary,
            "orphaned_vehicle_summary": orphaned_veh_summary,
            "orphaned_casualty_summary": orphaned_cas_summary,
            "inconsistent_severities": inconsistent_severities,
            "leaked_outcomes": leaked_outcomes,
            "midnight_substitutions": midnight_substitutions,
            "is_valid": is_valid,
        }
