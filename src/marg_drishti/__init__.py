"""MargDrishti - UK Road Safety Analytics and Severity Benchmarking.

Data foundation package for data ingestion, validation, Parquet conversion,
DuckDB modelling, and analytical data mart preparation.
"""

__version__ = "0.1.0"

from marg_drishti.config import PipelineConfig
from marg_drishti.validation import DataValidator, ValidationReport
from marg_drishti.conversion import ParquetConverter
from marg_drishti.database import DatabaseManager
from marg_drishti.pipeline import run_data_pipeline

__all__ = [
    "PipelineConfig",
    "DataValidator",
    "ValidationReport",
    "ParquetConverter",
    "DatabaseManager",
    "run_data_pipeline",
]
