"""DuckDB database initialization and analytical mart build manager."""

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import duckdb

from marg_drishti.config import PipelineConfig


class DatabaseManager:
    """Manages DuckDB connection, SQL execution, and table builds."""

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

        # Build research view if research parquet exists
        if self.config.research_collision_parquet.exists():
            res_path = str(self.config.research_collision_parquet).replace("\\", "/")
            self.con.execute(f"""
                CREATE OR REPLACE VIEW research_collisions_2020_2024 AS
                SELECT * FROM read_parquet('{res_path}')
            """)

        # Gather row counts for key tables/views
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
        """Verify that joins did not multiply rows and primary keys remain unique."""
        stg_count = self.con.execute("SELECT COUNT(*) FROM stg_collisions").fetchone()[0]
        mart_count = self.con.execute("SELECT COUNT(*) FROM mart_collision_analytical").fetchone()[0]
        outcomes_count = self.con.execute("SELECT COUNT(*) FROM mart_collision_outcomes").fetchone()[0]

        dup_mart = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM mart_collision_analytical
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        dup_veh_summary = self.con.execute("""
            SELECT COUNT(*) FROM (
                SELECT collision_index FROM agg_vehicle_summary
                GROUP BY collision_index HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        row_count_preserved = (stg_count == mart_count == outcomes_count)

        return {
            "stg_collisions_count": stg_count,
            "mart_analytical_count": mart_count,
            "mart_outcomes_count": outcomes_count,
            "row_count_preserved": row_count_preserved,
            "duplicate_mart_keys": dup_mart,
            "duplicate_vehicle_summary_keys": dup_veh_summary,
            "is_valid": row_count_preserved and (dup_mart == 0) and (dup_veh_summary == 0),
        }
