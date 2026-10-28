# MargDrishti Data Model Architecture

The MargDrishti data model is structured in layers using DuckDB and Apache Parquet. It enforces relational integrity, grain preservation, and strict separation between pre-crash predictive factors and post-crash casualty outcomes.

---

## 1. Relational Layers

```
Raw CSV Sources (data/raw/official_stats19/)
         │
         ▼ (Parquet Conversion: Snappy compression)
Parquet Files (data/processed/parquet/)
         │
         ▼ (DuckDB Views: Schema & Typed Columns)
Staging Layer (`stg_collisions`, `raw_vehicles`, `raw_casualties`)
         │
         ├──────────────────────────────────────────────┐
         ▼                                              ▼
Vehicle Summary (`agg_vehicle_summary`)     Casualty Summary (`agg_casualty_summary`)
[Grain: 1 row per collision]                [Grain: 1 row per collision]
         │                                              │
         ▼ (1:1 LEFT JOIN)                              ▼ (1:1 LEFT JOIN)
Analytical Mart (`mart_collision_analytical`)  Outcomes Mart (`mart_collision_outcomes`)
[Pre-crash features & severity target]       [Post-crash injury burden & casualty analysis]
```

---

## 2. Table and View Specifications

### 2.1 Staging Layer: `stg_collisions`
- **Source:** `raw_collisions`
- **Grain:** 1 row per collision (`collision_index` is unique).
- **Transformations:**
  - Standardizes `collision_index` and `collision_ref_no` as `VARCHAR`.
  - Derives typed dates (`collision_date`) and timestamps (`collision_timestamp`).
  - Maps numerical codes to descriptive category labels (`collision_severity_name`, `day_of_week_name`, `road_type_name`, `light_conditions_name`, `weather_conditions_name`, `road_surface_conditions_name`).
  - Derives binary severity target: `is_fatal_or_serious` (`1` if severity is Fatal (1) or Serious (2); `0` if Slight (3)).
  - Handles `-1` sentinel values cleanly by setting numeric nullable fields (e.g. `speed_limit_mph = NULL` when `speed_limit = -1`).

### 2.2 Vehicle Summary: `agg_vehicle_summary`
- **Source:** `raw_vehicles`
- **Grain:** Exactly 1 row per collision (`collision_index` PRIMARY KEY).
- **Design Rule:** In STATS19, collisions involve between 1 and multiple vehicles. A naive join between collision and vehicle tables would duplicate collision rows. To prevent row multiplication, vehicle-level records are aggregated strictly to the collision grain:
  - Vehicle mix counts: `pedal_cycle_count`, `motorcycle_count`, `car_taxi_count`, `bus_coach_count`, `goods_vehicle_count`, `hgv_count`.
  - Vehicle involvement flags: `has_pedal_cycle`, `has_motorcycle`, `has_bus_coach`, `has_hgv`, `has_escooter`, `has_two_wheeled_or_vulnerable_vehicle`.
  - Driver demographic summaries: `youngest_driver_age`, `oldest_driver_age`, `avg_driver_age`, `has_young_driver` (17-24), `has_older_driver` (70+).
  - Vehicle characteristics: `newest_vehicle_age`, `oldest_vehicle_age`, `avg_vehicle_age`, `max_engine_capacity_cc`.
  - Pre-impact dynamic manoeuvres: `has_skidding_or_overturning`, `has_vehicle_leaving_carriageway`, `has_towing_or_articulation`.

### 2.3 Casualty Summary: `agg_casualty_summary`
- **Source:** `raw_casualties`
- **Grain:** Exactly 1 row per collision (`collision_index` PRIMARY KEY).
- **Design Rule:** Casualty details are post-crash outcomes, not pre-crash predictors. This table is reserved exclusively for injury severity and statistical burden reporting:
  - Severity counts: `fatal_casualty_count`, `serious_casualty_count`, `slight_casualty_count`, `ksi_casualty_count`.
  - Casualty classification: `driver_casualty_count`, `passenger_casualty_count`, `pedestrian_casualty_count`, `cyclist_casualty_count`, `motorcyclist_casualty_count`.
  - Age demographics: `youngest_casualty_age`, `oldest_casualty_age`, `child_casualty_count`, `elderly_casualty_count`.

### 2.4 Analytical Mart: `mart_collision_analytical`
- **Grain:** 1 row per collision (`collision_index`).
- **Join:** `stg_collisions c LEFT JOIN agg_vehicle_summary v ON c.collision_index = v.collision_index`.
- **Integrity Guarantee:** The row count matches `stg_collisions` exactly (513,801 rows). Zero row multiplication occurs.
- **Separation of Concerns:** Contains **zero casualty outcome columns** or post-crash features, preventing data leakage during future statistical modelling.

### 2.5 Outcomes Mart: `mart_collision_outcomes`
- **Grain:** 1 row per collision (`collision_index`).
- **Join:** `stg_collisions c LEFT JOIN agg_casualty_summary k ON c.collision_index = k.collision_index`.
- **Purpose:** Dedicated to casualty severity analytics, pedestrian casualty impact, and public health road safety burden reporting.
