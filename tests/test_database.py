"""Unit tests for DuckDB database tables, views, and analytical marts."""

import duckdb
import pytest

from marg_drishti.config import PipelineConfig
from marg_drishti.conversion import ParquetConverter
from marg_drishti.database import DatabaseManager


@pytest.fixture
def converted_db(synthetic_data_dir):
    """Set up converted parquet files and DuckDB database for testing."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    converter = ParquetConverter(config)
    converter.convert_all_official(overwrite=True)
    converter.close()

    db = DatabaseManager(config)
    db.build_database()
    yield db
    db.close()


def test_row_count_preservation_and_no_join_multiplication(converted_db):
    """Ensure joining vehicle summary to collision mart strictly preserves row count."""
    integrity = converted_db.verify_integrity()

    assert integrity["is_valid"] is True
    assert integrity["row_count_preserved"] is True
    assert integrity["stg_collisions_count"] == 5
    assert integrity["mart_analytical_count"] == 5
    assert integrity["mart_outcomes_count"] == 5
    assert integrity["duplicate_mart_keys"] == 0
    assert integrity["duplicate_vehicle_summary_keys"] == 0


def test_vehicle_summary_aggregations(converted_db):
    """Verify vehicle summary correctly computes counts and presence flags at collision grain."""
    res = converted_db.con.execute("""
        SELECT
            collision_index,
            total_vehicles_in_dataset,
            has_motorcycle,
            has_hgv,
            has_pedal_cycle,
            youngest_driver_age,
            has_young_driver
        FROM agg_vehicle_summary
        ORDER BY collision_index
    """).fetchall()

    assert len(res) == 5

    # Collision 1: 2 vehicles (Car + Motorcycle), young driver age 22
    c1 = res[0]
    assert c1[0] == "202101000001"
    assert c1[1] == 2  # 2 vehicles
    assert c1[2] == 1  # has_motorcycle
    assert c1[3] == 0  # no HGV
    assert c1[4] == 0  # no pedal cycle
    assert c1[5] == 22 # youngest driver age
    assert c1[6] == 1  # has_young_driver

    # Collision 2: 1 vehicle (HGV)
    c2 = res[1]
    assert c2[0] == "202101000002"
    assert c2[1] == 1
    assert c2[3] == 1  # has_hgv

    # Collision 3: 3 vehicles (Car, Van, Pedal cycle)
    c3 = res[2]
    assert c3[0] == "202101000003"
    assert c3[1] == 3
    assert c3[4] == 1  # has_pedal_cycle


def test_casualty_outcomes_separated_from_analytical_mart(converted_db):
    """Ensure analytical mart does NOT contain casualty outcome columns."""
    analytical_cols = [
        c[0] for c in converted_db.con.execute("DESCRIBE SELECT * FROM mart_collision_analytical").fetchall()
    ]
    outcome_cols = [
        c[0] for c in converted_db.con.execute("DESCRIBE SELECT * FROM mart_collision_outcomes").fetchall()
    ]

    # Outcome columns must be in mart_collision_outcomes
    assert "fatal_casualty_count" in outcome_cols
    assert "serious_casualty_count" in outcome_cols
    assert "has_fatal_casualty" in outcome_cols

    # Outcome columns must NOT be in mart_collision_analytical
    assert "fatal_casualty_count" not in analytical_cols
    assert "serious_casualty_count" not in analytical_cols
    assert "has_fatal_casualty" not in analytical_cols


def test_sentinel_values_handled_properly(converted_db):
    """Ensure -1 codes in speed limit are treated cleanly as NULL in speed_limit_mph."""
    res = converted_db.con.execute("""
        SELECT speed_limit, speed_limit_mph
        FROM stg_collisions
        WHERE collision_index = '202101000003'
    """).fetchone()

    # Raw speed_limit retains -1 sentinel code
    assert res[0] == -1
    # Derived clean speed_limit_mph is NULL (not zero!)
    assert res[1] is None
