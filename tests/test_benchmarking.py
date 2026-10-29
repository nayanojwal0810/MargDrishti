"""Unit and integration tests for MargDrishti case-mix-adjusted severity benchmarking."""

import subprocess
import sys
import numpy as np
import pandas as pd
import pytest

from marg_drishti.benchmarking import (
    BENCHMARK_FEATURES,
    calculate_authority_benchmark,
    compute_out_of_fold_probabilities,
    format_category_value,
    format_feature_matrix,
    is_valid_authority_code,
    is_valid_severity_code,
    run_severity_benchmark,
)
from marg_drishti.config import PipelineConfig
from marg_drishti.conversion import ParquetConverter
from marg_drishti.database import DatabaseManager


@pytest.fixture
def synthetic_mart_df(synthetic_data_dir):
    """Provide mart_collision_analytical dataframe from the synthetic database fixture."""
    config = PipelineConfig(base_dir=synthetic_data_dir["base_dir"])
    converter = ParquetConverter(config)
    converter.convert_all_official(overwrite=True)
    converter.close()

    db = DatabaseManager(config)
    db.build_database()
    df = db.con.execute("SELECT * FROM mart_collision_analytical").df()
    db.close()
    return df


def test_severity_and_authority_validation_helpers():
    """Verify severity and authority code validation logic."""
    # Valid severity codes
    assert is_valid_severity_code(1) is True
    assert is_valid_severity_code(2) is True
    assert is_valid_severity_code(3) is True
    assert is_valid_severity_code("1") is True
    assert is_valid_severity_code(2.0) is True

    # Invalid severity codes
    assert is_valid_severity_code(9) is False
    assert is_valid_severity_code(-1) is False
    assert is_valid_severity_code(None) is False
    assert is_valid_severity_code(np.nan) is False
    assert is_valid_severity_code("") is False
    assert is_valid_severity_code("invalid") is False

    # Valid authority codes
    assert is_valid_authority_code("E09000001") is True
    assert is_valid_authority_code("E06000002") is True

    # Invalid authority codes
    assert is_valid_authority_code(None) is False
    assert is_valid_authority_code(np.nan) is False
    assert is_valid_authority_code("") is False
    assert is_valid_authority_code("   ") is False
    assert is_valid_authority_code("-1") is False
    assert is_valid_authority_code(-1) is False


def test_format_category_value_preserves_sentinels_and_handles_missing():
    """Verify categorical string formatting handles missing, sentinels, and floats."""
    assert format_category_value(-1) == "-1"
    assert format_category_value("-1") == "-1"
    assert format_category_value(-1.0) == "-1"
    assert format_category_value(None) == "missing"
    assert format_category_value(np.nan) == "missing"
    assert format_category_value("") == "missing"
    assert format_category_value(14.0) == "14"
    assert format_category_value(14) == "14"
    assert format_category_value("Rural") == "Rural"


def test_format_feature_matrix(synthetic_mart_df):
    """Verify feature matrix contains all 20 required benchmark features as strings."""
    X = format_feature_matrix(synthetic_mart_df, BENCHMARK_FEATURES)
    assert list(X.columns) == BENCHMARK_FEATURES
    assert len(X) == len(synthetic_mart_df)
    for col in BENCHMARK_FEATURES:
        assert all(isinstance(v, str) for v in X[col])


def test_benchmarking_on_synthetic_data(synthetic_mart_df):
    """Verify end-to-end benchmarking on the synthetic dataset."""
    df = synthetic_mart_df
    benchmark_df, summary, oof_probs = run_severity_benchmark(df, random_state=42)

    # 1. Total records: 6; eligible (known severity 1,2,3): 5; excluded (code 9): 1
    assert summary["record_counts"]["total_collision_records"] == 6
    assert summary["record_counts"]["eligible_collision_count"] == 5
    assert summary["record_counts"]["missing_or_invalid_severity_count"] == 1
    assert summary["record_counts"]["invalid_or_missing_authority_count"] == 0
    assert summary["record_counts"]["authorities_benchmarked_count"] == 2

    # 2. Minority class adaptation: slight has 2 collisions, so max folds reduces to 2
    assert summary["model_settings"]["folds_used"] == 2
    assert summary["model_settings"]["max_folds"] == 5

    # 3. Exactly one finite probability per eligible record in [0, 1]
    assert len(oof_probs) == 5
    assert np.all(np.isfinite(oof_probs))
    assert np.all((oof_probs >= 0.0) & (oof_probs <= 1.0))

    # 4. Schema verification
    expected_cols = [
        "authority_code",
        "collision_count",
        "known_severity_collision_count",
        "missing_or_invalid_severity_count",
        "observed_ksi_count",
        "observed_ksi_share_pct",
        "expected_ksi_count",
        "expected_ksi_share_pct",
        "observed_expected_ratio",
        "case_mix_adjusted_ksi_index",
    ]
    assert list(benchmark_df.columns) == expected_cols

    # 5. Row counts and collision preservation
    # Authority E09000001: 3 collisions, all 3 known (2 KSI, 1 slight)
    # Authority E09000002: 3 collisions, 2 known (1 KSI, 1 slight), 1 invalid (code 9)
    auth1 = benchmark_df[benchmark_df["authority_code"] == "E09000001"].iloc[0]
    assert auth1["collision_count"] == 3
    assert auth1["known_severity_collision_count"] == 3
    assert auth1["missing_or_invalid_severity_count"] == 0
    assert auth1["observed_ksi_count"] == 2
    assert auth1["observed_ksi_share_pct"] == pytest.approx(66.67, abs=0.01)

    auth2 = benchmark_df[benchmark_df["authority_code"] == "E09000002"].iloc[0]
    assert auth2["collision_count"] == 3
    assert auth2["known_severity_collision_count"] == 2
    assert auth2["missing_or_invalid_severity_count"] == 1
    assert auth2["observed_ksi_count"] == 1
    assert auth2["observed_ksi_share_pct"] == pytest.approx(50.0, abs=0.01)

    # 6. Sum of probabilities equals expected KSI count per authority
    # Eligible rows for E09000001 are indices 0, 1, 2
    expected_auth1 = oof_probs[0] + oof_probs[1] + oof_probs[2]
    assert auth1["expected_ksi_count"] == pytest.approx(expected_auth1, abs=0.001)

    # Eligible rows for E09000002 are indices 3, 4
    expected_auth2 = oof_probs[3] + oof_probs[4]
    assert auth2["expected_ksi_count"] == pytest.approx(expected_auth2, abs=0.001)

    # 7. Metric reconciliation on every row
    for _, row in benchmark_df.iterrows():
        c_count = row["collision_count"]
        known = row["known_severity_collision_count"]
        missing = row["missing_or_invalid_severity_count"]
        obs_ksi = row["observed_ksi_count"]
        exp_ksi = row["expected_ksi_count"]
        obs_share = row["observed_ksi_share_pct"]
        exp_share = row["expected_ksi_share_pct"]
        ratio = row["observed_expected_ratio"]
        idx = row["case_mix_adjusted_ksi_index"]

        assert c_count == known + missing
        if known > 0:
            assert obs_share == pytest.approx((obs_ksi / known) * 100.0, abs=0.01)
            assert exp_share == pytest.approx((exp_ksi / known) * 100.0, abs=0.01)
        if exp_ksi > 0:
            assert ratio == pytest.approx(obs_ksi / exp_ksi, abs=0.01)
            assert idx == pytest.approx(ratio * 100.0, abs=0.01)


def test_missing_and_invalid_authority_codes_reported_and_excluded(synthetic_mart_df):
    """Verify records with missing or invalid authority codes are excluded from named comparisons."""
    df = synthetic_mart_df.copy()

    # Append 4 synthetic rows with invalid authority codes
    invalid_rows = []
    for code in [None, "", "   ", "-1"]:
        row = df.iloc[0].copy()
        row["collision_index"] = f"INV_{code}"
        row["local_authority_highway_current"] = code
        invalid_rows.append(row)

    df_augmented = pd.concat([df, pd.DataFrame(invalid_rows)], ignore_index=True)
    benchmark_df, summary, _ = run_severity_benchmark(df_augmented)

    # 4 records with invalid authority should be reported
    assert summary["record_counts"]["invalid_or_missing_authority_count"] == 4

    # None of the invalid codes should appear in named authority benchmarks
    benchmark_authorities = set(benchmark_df["authority_code"])
    assert None not in benchmark_authorities
    assert "" not in benchmark_authorities
    assert "   " not in benchmark_authorities
    assert "-1" not in benchmark_authorities
    assert benchmark_authorities == {"E09000001", "E09000002"}


def test_model_rejects_single_outcome_class(synthetic_mart_df):
    """Verify clear ValueError when input cannot support cross-validation."""
    df = synthetic_mart_df.copy()

    # Case 1: All records have the same outcome class (KSI=1)
    df["collision_severity"] = 1
    with pytest.raises(ValueError, match="at least 2 outcome classes"):
        run_severity_benchmark(df)

    # Case 2: Only 1 observation in minority class (< 2)
    df.loc[0, "collision_severity"] = 3  # 1 Slight
    df.loc[1:, "collision_severity"] = 1  # 5 Fatal
    with pytest.raises(ValueError, match="at least two observations are required"):
        run_severity_benchmark(df)


def test_zero_expected_ksi_produces_safe_null(synthetic_mart_df):
    """Verify safe denominator handling when expected KSI is zero."""
    df = synthetic_mart_df.copy()
    eligible_mask = df["collision_severity"].isin([1, 2, 3])
    # Zero probabilities
    zero_probs = np.zeros(eligible_mask.sum(), dtype=float)

    benchmark_df = calculate_authority_benchmark(df, eligible_mask, zero_probs)

    for _, row in benchmark_df.iterrows():
        assert row["expected_ksi_count"] == 0.0
        assert row["observed_expected_ratio"] is None
        assert row["case_mix_adjusted_ksi_index"] is None


def test_benchmark_reproducibility(synthetic_mart_df):
    """Verify identical out-of-fold probabilities and metrics with the same random seed."""
    df = synthetic_mart_df.copy()

    df1, sum1, probs1 = run_severity_benchmark(df, random_state=42)
    df2, sum2, probs2 = run_severity_benchmark(df, random_state=42)

    assert np.allclose(probs1, probs2)
    pd.testing.assert_frame_equal(df1, df2)
    assert sum1["overall_metrics"] == sum2["overall_metrics"]


def test_run_benchmark_cli_error_handling(tmp_path):
    """Verify run_benchmark.py stops with clear error when database is missing."""
    from marg_drishti.config import PROJECT_ROOT

    script_path = PROJECT_ROOT / "run_benchmark.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()
