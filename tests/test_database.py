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
    assert integrity["stg_collisions_count"] == 6
    assert integrity["mart_analytical_count"] == 6
    assert integrity["mart_outcomes_count"] == 6
    assert integrity["duplicate_mart_keys"] == 0
    assert integrity["duplicate_vehicle_summary_keys"] == 0


def test_severity_classification_and_null_handling(converted_db):
    """Verify severity mapping produces 1 for Fatal/Serious, 0 for Slight, and NULL for unexpected codes."""
    rows = converted_db.con.execute("""
        SELECT
            collision_index,
            collision_severity,
            collision_severity_name,
            is_fatal_or_serious
        FROM stg_collisions
        ORDER BY collision_index
    """).fetchall()

    assert len(rows) == 6

    # Collision 1: Fatal (1) -> 'Fatal', 1
    assert rows[0][1] == 1
    assert rows[0][2] == "Fatal"
    assert rows[0][3] == 1

    # Collision 2: Serious (2) -> 'Serious', 1
    assert rows[1][1] == 2
    assert rows[1][2] == "Serious"
    assert rows[1][3] == 1

    # Collision 3: Slight (3) -> 'Slight', 0
    assert rows[2][1] == 3
    assert rows[2][2] == "Slight"
    assert rows[2][3] == 0

    # Collision 4: Slight (3) -> 'Slight', 0
    assert rows[3][1] == 3
    assert rows[3][2] == "Slight"
    assert rows[3][3] == 0

    # Collision 5: Serious (2) -> 'Serious', 1
    assert rows[4][1] == 2
    assert rows[4][2] == "Serious"
    assert rows[4][3] == 1

    # Collision 6: Invalid/Unknown (9) -> NULL, NULL (never default to Slight / 0!)
    assert rows[5][1] == 9
    assert rows[5][2] is None
    assert rows[5][3] is None


def test_collision_time_handling_no_midnight_default(converted_db):
    """Verify that missing or unparseable time fields result in NULL timestamp and hour, without defaulting to midnight."""
    rows = converted_db.con.execute("""
        SELECT
            collision_index,
            collision_date,
            collision_time,
            collision_timestamp,
            collision_hour
        FROM stg_collisions
        ORDER BY collision_index
    """).fetchall()

    assert len(rows) == 6

    # Collision 1: Valid time ('14:30') -> exact timestamp preserving recorded minutes
    c1_ts = rows[0][3]
    assert c1_ts is not None
    assert c1_ts.strftime("%Y-%m-%d %H:%M:%S") == "2021-03-15 14:30:00"
    assert c1_ts.minute == 30, "collision_timestamp must preserve exact minutes (30), not truncated to 00"
    assert c1_ts.strftime("%H:%M:%S") != "14:00:00", "collision_timestamp must not be truncated to hour"
    assert rows[0][4] == 14

    # Collision 4: Missing time ('') -> date preserved, but timestamp and hour are NULL
    assert rows[3][1].isoformat() == "2022-07-04"
    assert rows[3][2] is None, "Missing time must result in NULL collision_time!"
    assert rows[3][3] is None, "Missing time must not be defaulted to midnight!"
    assert rows[3][4] is None

    # Collision 5: Invalid time ('99:99') -> date preserved, but timestamp and hour are NULL
    assert rows[4][1].isoformat() == "2023-11-12"
    assert rows[4][2] is None, "Invalid time must result in NULL collision_time!"
    assert rows[4][3] is None, "Invalid time must not be defaulted to midnight!"
    assert rows[4][4] is None


def test_vehicle_category_corrections_and_aggregations(converted_db):
    """Verify vehicle category mappings: vehicle_type 16 is ridden horse, NOT pedal cycle; mobility scooters and PLEVs are distinguished."""
    res = converted_db.con.execute("""
        SELECT
            collision_index,
            total_vehicles_in_dataset,
            pedal_cycle_count,
            has_pedal_cycle,
            ridden_horse_count,
            has_ridden_horse,
            mobility_scooter_count,
            has_mobility_scooter,
            personal_transporter_count,
            has_personal_transporter,
            youngest_driver_age,
            has_young_driver
        FROM agg_vehicle_summary
        ORDER BY collision_index
    """).fetchall()

    assert len(res) == 6

    # Collision 1: 2 vehicles (Car + Motorcycle), driver age 22
    c1 = res[0]
    assert c1[0] == "202101000001"
    assert c1[1] == 2
    assert c1[2] == 0  # no pedal cycles
    assert c1[3] == 0
    assert c1[4] == 0  # no ridden horses
    assert c1[5] == 0
    assert c1[10] == 22
    assert c1[11] == 1

    # Collision 3: 4 vehicles (Car, Van, Pedal cycle type 1, Ridden horse type 16)
    c3 = res[2]
    assert c3[0] == "202101000003"
    assert c3[1] == 4
    # Check that type 16 is NOT counted in pedal cycle!
    assert c3[2] == 1, "pedal_cycle_count must be 1 (only vehicle_type = 1)"
    assert c3[3] == 1
    # Check that type 16 is counted as ridden horse!
    assert c3[4] == 1, "ridden_horse_count must be 1 (vehicle_type = 16)"
    assert c3[5] == 1

    # Collision 4: 1 vehicle (Mobility scooter type 22)
    c4 = res[3]
    assert c4[0] == "202201000004"
    assert c4[1] == 1
    assert c4[6] == 1, "mobility_scooter_count must be 1"
    assert c4[7] == 1

    # Collision 5: 2 vehicles (Bus type 11 + PLEV type 33 / escooter_flag 1)
    c5 = res[4]
    assert c5[0] == "202301000005"
    assert c5[1] == 2
    assert c5[8] == 1, "personal_transporter_count must be 1"
    assert c5[9] == 1


def test_geographic_identifiers_in_analytical_mart(converted_db):
    """Verify geographic identifiers (ONS district and highway current) are present and populated."""
    row = converted_db.con.execute("""
        SELECT
            collision_index,
            local_authority_ons_district,
            local_authority_highway_current
        FROM mart_collision_analytical
        WHERE collision_index = '202101000001'
    """).fetchone()

    assert row[1] == "E09000001"
    assert row[2] == "E09000001"


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
    assert "has_serious_casualty" in outcome_cols

    # Outcome columns must NOT be in mart_collision_analytical
    assert "fatal_casualty_count" not in analytical_cols
    assert "serious_casualty_count" not in analytical_cols
    assert "has_fatal_casualty" not in analytical_cols
    assert "has_serious_casualty" not in analytical_cols
    assert "total_casualties" not in analytical_cols
    assert "pedestrian_casualty_count" not in analytical_cols


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


def test_summary_row_completeness_and_key_validity(converted_db):
    """Verify that summary tables have 100% collision coverage with valid, non-blank keys."""
    integrity = converted_db.verify_integrity()

    assert integrity["is_valid"] is True
    assert integrity["summary_coverage_complete"] is True
    assert integrity["total_blank_keys"] == 0
    assert integrity["unmatched_veh_summary"] == 0
    assert integrity["unmatched_cas_summary"] == 0
    assert integrity["veh_summary_count"] == integrity["stg_collisions_count"]
    assert integrity["cas_summary_count"] == integrity["stg_collisions_count"]

