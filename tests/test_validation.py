"""Unit tests for DataValidator."""

import csv
from pathlib import Path
import pytest

from marg_drishti.config import PipelineConfig
from marg_drishti.validation import DataValidator


def test_validation_passes_on_valid_synthetic_data(synthetic_data_dir):
    """Ensure clean synthetic data passes all validation checks."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    assert report.is_valid is True
    assert len(report.errors) == 0
    assert report.duplicate_collision_ids == 0
    assert report.orphaned_vehicles == 0
    assert report.orphaned_casualties == 0
    assert report.row_counts["collision"] == 6
    assert report.row_counts["vehicle"] == 11
    assert report.row_counts["casualty"] == 7
    assert report.collisions_with_vehicles_pct == 100.0
    assert report.collisions_with_casualties_pct == 100.0


def test_validation_detects_missing_file(synthetic_data_dir):
    """Ensure missing CSV files trigger validation failure."""
    synthetic_data_dir["cas_csv"].unlink()
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    assert report.is_valid is False
    assert any("Required raw file is missing" in err for err in report.errors)


def test_validation_detects_duplicate_collision_ids(synthetic_data_dir):
    """Ensure duplicate primary keys in collision table trigger validation failure."""
    coll_csv = synthetic_data_dir["coll_csv"]

    # Append a duplicate row
    with open(coll_csv, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    dup_row = list(reader[1])  # Copy first data row
    with open(coll_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(dup_row)

    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    assert report.is_valid is False
    assert report.duplicate_collision_ids > 0
    assert any("duplicate collision_index" in err for err in report.errors)


def test_validation_detects_orphaned_vehicle_records(synthetic_data_dir):
    """Ensure foreign key violation in vehicle table triggers validation failure."""
    veh_csv = synthetic_data_dir["veh_csv"]

    with open(veh_csv, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    orphan_row = list(reader[1])
    orphan_row[0] = "999999999999"  # Non-existent collision_index
    with open(veh_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(orphan_row)

    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    assert report.is_valid is False
    assert report.orphaned_vehicles == 1
    assert any("orphaned vehicle records" in err for err in report.errors)


def test_validation_detects_orphaned_casualty_records(synthetic_data_dir):
    """Ensure foreign key violation in casualty table triggers validation failure."""
    cas_csv = synthetic_data_dir["cas_csv"]

    with open(cas_csv, "r", encoding="utf-8") as f:
        reader = list(csv.reader(f))
    orphan_row = list(reader[1])
    orphan_row[0] = "888888888888"  # Non-existent collision_index
    with open(cas_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(orphan_row)

    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    assert report.is_valid is False
    assert report.orphaned_casualties == 1
    assert any("orphaned casualty records" in err for err in report.errors)


def test_validation_reports_sentinel_unknown_codes(synthetic_data_dir):
    """Ensure -1 codes in speed_limit, junction_control etc. are captured as warnings."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    validator = DataValidator(config)
    report = validator.validate_csv_sources()
    validator.close()

    # In our synthetic collision data, row 3 has speed_limit = -1
    assert report.sentinel_unknown_values["collision"]["speed_limit"] == 1
    assert any("speed_limit" in w for w in report.warnings)
