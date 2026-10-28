"""High-performance CSV to Parquet conversion using DuckDB."""

from pathlib import Path
from typing import Dict, Optional
import duckdb

from marg_drishti.config import PipelineConfig


class ParquetConverter:
    """Converts raw official and research CSV files into compressed Parquet files."""

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.con = duckdb.connect()

    def close(self):
        """Close DuckDB connection."""
        self.con.close()

    def convert_csv_to_parquet(
        self,
        csv_path: Path,
        parquet_path: Path,
        compression: str = "snappy",
        overwrite: bool = True,
    ) -> Path:
        """Convert a single CSV file to Parquet format."""
        if not csv_path.exists():
            raise FileNotFoundError(f"Input CSV not found: {csv_path}")

        if parquet_path.exists() and not overwrite:
            return parquet_path

        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        csv_str = str(csv_path).replace("\\", "/")
        parquet_str = str(parquet_path).replace("\\", "/")

        query = f"""
            COPY (
                SELECT * FROM read_csv_auto('{csv_str}', header=True)
            ) TO '{parquet_str}' (
                FORMAT PARQUET,
                COMPRESSION '{compression}'
            )
        """
        self.con.execute(query)

        if not parquet_path.exists() or parquet_path.stat().st_size == 0:
            raise RuntimeError(f"Parquet conversion failed or produced empty file: {parquet_path}")

        return parquet_path

    def convert_all_official(self, overwrite: bool = True) -> Dict[str, Path]:
        """Convert all official STATS19 CSV files to Parquet."""
        self.config.ensure_directories()
        results = {}

        tasks = [
            ("collision", self.config.official_collision_csv, self.config.official_collision_parquet),
            ("vehicle", self.config.official_vehicle_csv, self.config.official_vehicle_parquet),
            ("casualty", self.config.official_casualty_csv, self.config.official_casualty_parquet),
        ]

        for name, csv_p, pq_p in tasks:
            pq = self.convert_csv_to_parquet(csv_p, pq_p, overwrite=overwrite)
            results[name] = pq

        return results

    def convert_research_dataset(self, overwrite: bool = True) -> Optional[Path]:
        """Convert research extracted UKdata.csv to Parquet if available."""
        if self.config.research_extracted_csv.exists():
            self.config.ensure_directories()
            return self.convert_csv_to_parquet(
                self.config.research_extracted_csv,
                self.config.research_collision_parquet,
                overwrite=overwrite,
            )
        return None
