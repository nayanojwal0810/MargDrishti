"""Unit tests for ParquetConverter."""

from pathlib import Path
import duckdb
import pytest

from marg_drishti.config import PipelineConfig
from marg_drishti.conversion import ParquetConverter


def test_parquet_conversion_official(synthetic_data_dir):
    """Test conversion of synthetic official CSV files to Parquet."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    converter = ParquetConverter(config)
    results = converter.convert_all_official(overwrite=True)
    converter.close()

    assert len(results) == 3
    for name, pq_path in results.items():
        assert pq_path.exists()
        assert pq_path.stat().st_size > 0

    # Query parquet directly to verify row counts
    con = duckdb.connect()
    coll_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{results['collision']}')").fetchone()[0]
    veh_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{results['vehicle']}')").fetchone()[0]
    cas_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{results['casualty']}')").fetchone()[0]
    con.close()

    assert coll_count == 6
    assert veh_count == 11
    assert cas_count == 7
