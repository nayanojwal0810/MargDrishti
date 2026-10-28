# MargDrishti Data Model Architecture

The MargDrishti data model is structured in layers using DuckDB and Apache Parquet. It enforces relational integrity, grain preservation, official DfT STATS19 category specifications, and strict separation between collision context variables and post-crash casualty outcomes.

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
[Collision context, vehicle mix & target]    [Post-crash injury burden & casualty analysis]
```

---

## 2. Table and View Specifications

### 2.1 Staging Layer: `stg_collisions`
- **Source:** `raw_collisions`
- **Grain:** 1 row per collision (`collision_index` is unique primary key).
- **Transformations & Rules:**
  - Standardizes `collision_index` and `collision_ref_no` as `VARCHAR`.
  - **Temporal Handling:**
    - Derives `collision_date` as `DATE`.
    - If `time` is valid, derives `collision_time` (`TIME`), exact `collision_timestamp` (`TIMESTAMP` preserving minutes), and `collision_hour` (`INTEGER`).
    - If `time` is missing or unparseable, `collision_time`, `collision_timestamp`, and `collision_hour` are strictly set to `NULL` while preserving `collision_date`.
    - **No Midnight Substitution:** Missing times are never replaced with `00:00:00`, preventing artificial distortion of nighttime collision patterns.
  - **Collision Severity & Binary Target:**
    - Fatal (`1`) &rarr; `collision_severity_name = 'Fatal'`, `is_fatal_or_serious = 1`
    - Serious (`2`) &rarr; `collision_severity_name = 'Serious'`, `is_fatal_or_serious = 1`
    - Slight (`3`) &rarr; `collision_severity_name = 'Slight'`, `is_fatal_or_serious = 0`
    - Unexpected / Invalid / Unknown codes &rarr; `collision_severity_name = NULL`, `is_fatal_or_serious = NULL` (strictly prevents defaulting unknown records to Slight).
  - **Geographic Identifiers:**
    - Includes `local_authority_ons_district` (primary validated 9-character ONS code; 100% coverage).
    - Includes `local_authority_highway_current` (current highway authority; 99.99% coverage).
    - Retains legacy `local_authority_district` for audit purposes (99.96% missing/deprecated).
  - Maps numerical codes to descriptive category labels (`day_of_week_name`, `road_type_name`, `light_conditions_name`, `weather_conditions_name`, `road_surface_conditions_name`).
  - Handles `-1` sentinel values cleanly by setting numeric nullable fields (e.g. `speed_limit_mph = NULL` when `speed_limit = -1`).

### 2.2 Vehicle Summary: `agg_vehicle_summary`
- **Source:** `raw_vehicles`
- **Grain:** Exactly 1 row per collision (`collision_index` PRIMARY KEY).
- **Design Rule:** Collisions involve 1 to many vehicles. To prevent row multiplication when joining with collisions, vehicle records are aggregated strictly to the collision grain.
- **Official Category Definitions:**
  - **Pedal Cycles:** Strictly `vehicle_type = 1` (`pedal_cycle_count`, `has_pedal_cycle`).
  - **Ridden Horses:** Strictly `vehicle_type = 16` (`ridden_horse_count`, `has_ridden_horse`). Note: STATS20 assigns code `16` to ridden horses; it is never conflated with pedal cycles.
  - **Mobility Scooters:** Strictly `vehicle_type = 22` (`mobility_scooter_count`, `has_mobility_scooter`).
  - **Personal Powered Transporters (PLEVs / e-scooters):** `vehicle_type = 33` or `escooter_flag = 1` (`personal_transporter_count`, `has_personal_transporter`).
  - **Motorcycles:** `vehicle_type IN (2, 3, 4, 5, 23, 97)` (`motorcycle_count`, `has_motorcycle`), with `electric_motorcycle_count` (`vehicle_type = 23`).
  - **Cars & Taxis:** `vehicle_type IN (8, 9)` (`car_taxi_count`, `has_car_taxi`).
  - **Vans / LGVs:** `vehicle_type = 19` (`van_lgv_count`, `has_van_lgv`).
  - **HGVs:** `vehicle_type IN (20, 21)` (`hgv_count`, `has_hgv`).
  - **Buses & Coaches:** `vehicle_type IN (10, 11)` (`bus_coach_count`, `has_bus_coach`).
  - **Other / Unknown Vehicles:** `vehicle_type IN (-1, 99)` (`unknown_vehicle_type_count`).
- **Driver Demographic Summaries:**
  - `youngest_driver_age`, `oldest_driver_age`, `avg_driver_age`.
  - Flags: `has_young_driver` (17–24 years), `has_older_driver` (70+ years).
- **Vehicle Characteristics & Incident Context / Event Variables:**
  - Vehicle age metrics (`newest_vehicle_age`, `oldest_vehicle_age`, `avg_vehicle_age`).
  - `max_engine_capacity_cc`.
  - Dynamic manoeuvre and event flags: `has_skidding_or_overturning`, `has_vehicle_leaving_carriageway`, `has_towing_or_articulation`, `has_hit_object_in_carriageway`, `has_hit_object_off_carriageway`.

### 2.3 Casualty Summary: `agg_casualty_summary`
- **Source:** `raw_casualties`
- **Grain:** Exactly 1 row per collision (`collision_index` PRIMARY KEY).
- **Design Rule:** Casualty details are post-crash consequences, not pre-crash predictors. This table is reserved exclusively for injury severity and statistical burden reporting.
- **Official Category Definitions:**
  - **Severity Metrics:** `fatal_casualty_count`, `serious_casualty_count`, `slight_casualty_count`, `ksi_casualty_count`.
  - **Severity Flags:** `has_fatal_casualty`, `has_serious_casualty`, `has_ksi_casualty`.
  - **Casualty Class:** `driver_rider_casualty_count` (`casualty_class = 1`), `passenger_casualty_count` (`casualty_class = 2`), `pedestrian_casualty_count` (`casualty_class = 3` or `casualty_type = 0`).
  - **Casualty Type Breakdown:**
    - Cyclists: `casualty_type = 1`
    - Motorcyclists: `casualty_type IN (2, 3, 4, 5, 23, 97)`
    - Car occupants: `casualty_type IN (8, 9)`
    - Bus/coach occupants: `casualty_type IN (10, 11)`
    - Goods vehicle occupants: `casualty_type IN (19, 20, 21, 98)`
    - Mobility scooter users: `casualty_type = 22`
    - Personal light electric vehicle (PLEV) users: `casualty_type = 33` or `escooter_flag = 1`
    - Horse riders: `casualty_type = 16`
  - **Vulnerable Road User Flag:** `has_vulnerable_user_casualty` (capturing pedestrians, cyclists, motorcyclists, horse riders, mobility scooters, and PLEVs).
  - **Age Demographics:** `youngest_casualty_age`, `oldest_casualty_age`, `child_casualty_count` (<16 years), `elderly_casualty_count` (65+ years).

### 2.4 Analytical Mart: `mart_collision_analytical`
- **Grain:** Exactly 1 row per collision (`collision_index`).
- **Join:** `stg_collisions c LEFT JOIN agg_vehicle_summary v ON c.collision_index = v.collision_index`.
- **Integrity Guarantee:** The row count matches `stg_collisions` exactly (513,801 rows). Zero row multiplication occurs.
- **Content & Event Variables:** Retains useful collision-context and event variables (such as skidding, objects struck, and vehicle departures from the carriageway) alongside environmental conditions and vehicle mix.
- **Feature Eligibility Notice:** Because the analytical mart encompasses incident context and crash-dynamic variables alongside pre-crash environmental attributes, **feature eligibility must be explicitly reviewed and filtered before any future model is trained**. Incident dynamics represent event characteristics rather than baseline pre-crash risk factors.
- **Separation of Concerns:** Strictly excludes all casualty outcome aggregates (fatal/serious casualty counts, casualty severity flags) and post-crash operational response fields (police attendance, injury-based recording flags) to prevent post-crash target leakage.

### 2.5 Outcomes Mart: `mart_collision_outcomes`
- **Grain:** Exactly 1 row per collision (`collision_index`).
- **Join:** `stg_collisions c LEFT JOIN agg_casualty_summary k ON c.collision_index = k.collision_index`.
- **Purpose:** Dedicated to casualty severity analytics, pedestrian casualty impact, and public health road safety burden reporting.
