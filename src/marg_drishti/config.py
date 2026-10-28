"""Configuration, schema definitions, and lookup codes for MargDrishti."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set


# STATS19 Sentinel code definitions
# -1 indicates "Data missing or out of range" / "Unallocated" across DfT datasets.
SENTINEL_UNKNOWN_CODE = -1

# Core column definitions required for official STATS19 datasets
COLLISION_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "collision_year",
    "collision_ref_no",
    "collision_severity",
    "number_of_vehicles",
    "number_of_casualties",
    "date",
    "day_of_week",
    "time",
    "first_road_class",
    "road_type",
    "speed_limit",
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "urban_or_rural_area",
]

VEHICLE_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "collision_year",
    "collision_ref_no",
    "vehicle_reference",
    "vehicle_type",
    "vehicle_manoeuvre",
    "sex_of_driver",
    "age_of_driver",
    "age_of_vehicle",
    "engine_capacity_cc",
]

CASUALTY_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "collision_year",
    "collision_ref_no",
    "vehicle_reference",
    "casualty_reference",
    "casualty_class",
    "sex_of_casualty",
    "age_of_casualty",
    "casualty_severity",
]

RESEARCH_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "collision_year",
    "collision_severity",
    "number_of_vehicles",
    "number_of_casualties",
    "date",
    "time",
]

# Code descriptions according to DfT STATS19 Data Dictionary
SEVERITY_LOOKUP: Dict[int, str] = {
    1: "Fatal",
    2: "Serious",
    3: "Slight",
}

ROAD_TYPE_LOOKUP: Dict[int, str] = {
    1: "Roundabout",
    2: "One way street",
    3: "Dual carriageway",
    6: "Single carriageway",
    7: "Slip road",
    9: "Unknown",
    -1: "Missing / Out of range",
}

LIGHT_CONDITIONS_LOOKUP: Dict[int, str] = {
    1: "Daylight",
    4: "Darkness - lights lit",
    5: "Darkness - lights unlit",
    6: "Darkness - no lighting",
    7: "Darkness - lighting unknown",
    -1: "Missing / Out of range",
}

WEATHER_CONDITIONS_LOOKUP: Dict[int, str] = {
    1: "Fine no high winds",
    2: "Raining no high winds",
    3: "Snowing no high winds",
    4: "Fine + high winds",
    5: "Raining + high winds",
    6: "Snowing + high winds",
    7: "Fog or mist",
    8: "Other",
    9: "Unknown",
    -1: "Missing / Out of range",
}

ROAD_SURFACE_LOOKUP: Dict[int, str] = {
    1: "Dry",
    2: "Wet or damp",
    3: "Snow",
    4: "Frost or ice",
    5: "Flood 3cm or deeper",
    6: "Oil or diesel",
    7: "Mud",
    9: "Unknown",
    -1: "Missing / Out of range",
}


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SQL_DIR = PROJECT_ROOT / "sql"


@dataclass
class PipelineConfig:
    """Configuration paths for MargDrishti data pipeline."""

    base_dir: Path = field(default_factory=lambda: Path.cwd())

    # Raw Data Paths
    raw_official_dir: Path = field(init=False)
    raw_paper_dir: Path = field(init=False)
    official_collision_csv: Path = field(init=False)
    official_vehicle_csv: Path = field(init=False)
    official_casualty_csv: Path = field(init=False)
    research_archive_rar: Path = field(init=False)
    research_extracted_csv: Path = field(init=False)

    # Processed Data Paths
    processed_dir: Path = field(init=False)
    parquet_dir: Path = field(init=False)
    official_collision_parquet: Path = field(init=False)
    official_vehicle_parquet: Path = field(init=False)
    official_casualty_parquet: Path = field(init=False)
    research_collision_parquet: Path = field(init=False)

    # Database Path
    duckdb_path: Path = field(init=False)

    # SQL Directory (defaults to project sql directory)
    sql_dir: Path = DEFAULT_SQL_DIR

    def __post_init__(self):
        # Resolve raw paths
        self.raw_official_dir = self.base_dir / "data" / "raw" / "official_stats19"
        self.raw_paper_dir = self.base_dir / "data" / "raw" / "paper_replication"

        self.official_collision_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-collision-last-5-years.csv"
        )
        self.official_vehicle_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-vehicle-last-5-years.csv"
        )
        self.official_casualty_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-casualty-last-5-years.csv"
        )

        self.research_archive_rar = self.raw_paper_dir / "journal.pone.0347873.s002.rar"
        self.research_extracted_csv = (
            self.base_dir / ".local_audit" / "extracted" / "UKdata.csv"
        )

        # Resolve processed paths
        self.processed_dir = self.base_dir / "data" / "processed"
        self.parquet_dir = self.processed_dir / "parquet"
        self.official_collision_parquet = self.parquet_dir / "official_collision_2021_2025.parquet"
        self.official_vehicle_parquet = self.parquet_dir / "official_vehicle_2021_2025.parquet"
        self.official_casualty_parquet = self.parquet_dir / "official_casualty_2021_2025.parquet"
        self.research_collision_parquet = self.parquet_dir / "research_collision_2020_2024.parquet"

        self.duckdb_path = self.processed_dir / "marg_drishti.duckdb"

    def ensure_directories(self) -> None:
        """Create necessary processed output directories."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
