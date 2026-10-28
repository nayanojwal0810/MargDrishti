"""Integration tests for the complete MargDrishti pipeline."""

from pathlib import Path
import pytest

from marg_drishti.config import PipelineConfig
from marg_drishti.pipeline import run_data_pipeline
from tests.conftest import compute_file_hash


def test_full_pipeline_synthetic_execution_and_raw_data_immutability(synthetic_data_dir):
    """Run full pipeline on synthetic data and verify that raw data remains strictly unchanged."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])

    # Compute checksums before running pipeline
    hashes_before = {
        "coll": compute_file_hash(synthetic_data_dir["coll_csv"]),
        "veh": compute_file_hash(synthetic_data_dir["veh_csv"]),
        "cas": compute_file_hash(synthetic_data_dir["cas_csv"]),
    }

    # Execute pipeline
    result = run_data_pipeline(config=config, overwrite_parquet=True)

    # 1. Assert pipeline success
    assert result["success"] is True
    assert result["integrity"]["is_valid"] is True
    assert result["integrity"]["summary_coverage_complete"] is True
    assert result["integrity"]["total_blank_keys"] == 0
    assert result["integrity"]["veh_summary_count"] == 6
    assert result["integrity"]["cas_summary_count"] == 6
    assert result["row_counts"]["stg_collisions"] == 6
    assert result["row_counts"]["mart_collision_analytical"] == 6
    assert result["row_counts"]["mart_collision_outcomes"] == 6

    # 2. Assert raw data files remain strictly unchanged
    hashes_after = {
        "coll": compute_file_hash(synthetic_data_dir["coll_csv"]),
        "veh": compute_file_hash(synthetic_data_dir["veh_csv"]),
        "cas": compute_file_hash(synthetic_data_dir["cas_csv"]),
    }

    assert hashes_before == hashes_after, "Raw data files were modified during pipeline execution!"
