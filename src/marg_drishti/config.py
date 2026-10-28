"""Configuration, schema definitions, and lookup codes for MargDrishti.

All definitions align with the official UK Department for Transport STATS19
and STATS20 specifications.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


# STATS19 Sentinel code definitions
# -1 indicates "Data missing or out of range" / "Unallocated" across DfT datasets.
SENTINEL_UNKNOWN_CODE = -1

# Core column definitions required for official STATS19 datasets
# Covers every field utilized across all SQL staging, aggregations, and mart definitions
COLLISION_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "collision_year",
    "collision_ref_no",
    "date",
    "time",
    "day_of_week",
    "collision_severity",
    "first_road_class",
    "first_road_number",
    "road_type",
    "speed_limit",
    "junction_detail",
    "junction_control",
    "light_conditions",
    "weather_conditions",
    "road_surface_conditions",
    "urban_or_rural_area",
    "latitude",
    "longitude",
    "location_easting_osgr",
    "location_northing_osgr",
    "police_force",
    "local_authority_district",
    "local_authority_ons_district",
    "local_authority_highway",
    "local_authority_highway_current",
    "lsoa_of_accident_location",
    "number_of_vehicles",
    "number_of_casualties",
    "did_police_officer_attend_scene_of_accident",
    "enhanced_severity_collision",
    "collision_injury_based",
]

VEHICLE_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "vehicle_reference",
    "vehicle_type",
    "escooter_flag",
    "sex_of_driver",
    "age_of_driver",
    "age_of_vehicle",
    "engine_capacity_cc",
    "towing_and_articulation",
    "skidding_and_overturning",
    "vehicle_leaving_carriageway",
    "hit_object_in_carriageway",
    "hit_object_off_carriageway",
]

CASUALTY_REQUIRED_COLUMNS: List[str] = [
    "collision_index",
    "casualty_reference",
    "casualty_class",
    "casualty_severity",
    "casualty_type",
    "age_of_casualty",
    "escooter_flag",
]

# Code descriptions according to DfT STATS19 / STATS20 Data Dictionary
SEVERITY_LOOKUP: Dict[int, str] = {
    1: "Fatal",
    2: "Serious",
    3: "Slight",
}

# Official STATS19 Vehicle Type Specification
VEHICLE_TYPE_LOOKUP: Dict[int, str] = {
    1: "Pedal cycle",
    2: "Motorcycle 50cc and under",
    3: "Motorcycle 125cc and under",
    4: "Motorcycle over 125cc and up to 500cc",
    5: "Motorcycle over 500cc",
    8: "Taxi / Private hire car",
    9: "Car",
    10: "Minibus (8 - 16 passenger seats)",
    11: "Bus or coach (17 or more pass seats)",
    16: "Ridden horse",
    17: "Agricultural vehicle",
    18: "Tram",
    19: "Van / Goods 3.5 tonnes mgw and under",
    20: "Goods over 3.5t. and under 7.5t",
    21: "Goods 7.5 tonnes mgw and over (HGV)",
    22: "Mobility scooter",
    23: "Electric motorcycle",
    33: "Personal light electric vehicle (PLEV)",
    90: "Other vehicle",
    97: "Motorcycle - unknown cc",
    98: "Goods vehicle - unknown weight",
    99: "Unknown vehicle type",
    -1: "Missing / Out of range",
}

# Official STATS19 Casualty Type Specification
CASUALTY_TYPE_LOOKUP: Dict[int, str] = {
    0: "Pedestrian",
    1: "Cyclist",
    2: "Motorcycle 50cc and under occupant",
    3: "Motorcycle 125cc and under occupant",
    4: "Motorcycle 125cc-500cc occupant",
    5: "Motorcycle over 500cc occupant",
    8: "Taxi occupant",
    9: "Car occupant",
    10: "Minibus occupant",
    11: "Bus or coach occupant",
    16: "Horse rider",
    17: "Agricultural vehicle occupant",
    18: "Tram occupant",
    19: "Van / LGV occupant",
    20: "Goods vehicle 3.5t-7.5t occupant",
    21: "Heavy goods vehicle (HGV) occupant",
    22: "Mobility scooter rider",
    23: "Electric motorcycle occupant",
    33: "Personal light electric vehicle (PLEV) rider",
    90: "Other vehicle occupant",
    97: "Motorcycle (unknown cc) occupant",
    98: "Goods vehicle (unknown weight) occupant",
    99: "Unknown vehicle occupant",
    -1: "Missing / Out of range",
}

CASUALTY_CLASS_LOOKUP: Dict[int, str] = {
    1: "Driver or rider",
    2: "Vehicle or pillion passenger",
    3: "Pedestrian",
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
    """Configuration paths for MargDrishti official data pipeline."""

    base_dir: Path = field(default_factory=lambda: Path.cwd())

    # Raw Data Paths (Official STATS19 CSVs only)
    raw_official_dir: Path = field(init=False)
    official_collision_csv: Path = field(init=False)
    official_vehicle_csv: Path = field(init=False)
    official_casualty_csv: Path = field(init=False)

    # Processed Data Paths (Parquet)
    processed_dir: Path = field(init=False)
    parquet_dir: Path = field(init=False)
    official_collision_parquet: Path = field(init=False)
    official_vehicle_parquet: Path = field(init=False)
    official_casualty_parquet: Path = field(init=False)

    # Database Path
    duckdb_path: Path = field(init=False)

    # SQL Directory (defaults to project sql directory)
    sql_dir: Path = DEFAULT_SQL_DIR

    def __post_init__(self):
        # Resolve raw official paths
        self.raw_official_dir = self.base_dir / "data" / "raw" / "official_stats19"
        self.official_collision_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-collision-last-5-years.csv"
        )
        self.official_vehicle_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-vehicle-last-5-years.csv"
        )
        self.official_casualty_csv = (
            self.raw_official_dir / "dft-road-casualty-statistics-casualty-last-5-years.csv"
        )

        # Resolve processed paths
        self.processed_dir = self.base_dir / "data" / "processed"
        self.parquet_dir = self.processed_dir / "parquet"
        self.official_collision_parquet = self.parquet_dir / "official_collision_2021_2025.parquet"
        self.official_vehicle_parquet = self.parquet_dir / "official_vehicle_2021_2025.parquet"
        self.official_casualty_parquet = self.parquet_dir / "official_casualty_2021_2025.parquet"

        self.duckdb_path = self.processed_dir / "marg_drishti.duckdb"

    def ensure_directories(self) -> None:
        """Create necessary processed output directories."""
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_dir.mkdir(parents=True, exist_ok=True)
