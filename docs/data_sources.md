# Data Sources and Schema Documentation

MargDrishti operates exclusively on official UK road-casualty records published by the Department for Transport (DfT).

---

## 1. Official STATS19 Road Casualty Statistics

The Department for Transport collects road traffic collision records reported by police forces across Great Britain via the STATS19 reporting system.

- **Source:** [UK Department for Transport - Road Casualty Statistics](https://www.gov.uk/government/collections/road-accidents-and-safety-statistics)
- **Official Specification:** [STATS19 Forms and Guidance](https://www.gov.uk/government/publications/stats19-forms-and-guidance)
- **Snapshot Period:** 2021–2025 (rolling 5-year official release)
- **Format:** CSV files ingested, validated, and converted to Apache Parquet
- **Reporting Scope:** Personal injury collisions occurring on public roads in Great Britain resulting in injury or death reported to the police.

### File Descriptions

1. **Collisions (`dft-road-casualty-statistics-collision-last-5-years.csv`):**
   - **Grain:** 1 row per reported collision (`collision_index`).
   - **Row Count:** 513,801 records.
   - **Key Attributes:** Collision date, time, severity (Fatal, Serious, Slight), speed limit, road type, road classification, weather conditions, light conditions, road surface conditions, urban/rural classification, geographic coordinates.

2. **Vehicles (`dft-road-casualty-statistics-vehicle-last-5-years.csv`):**
   - **Grain:** 1 row per vehicle involved in a collision (`collision_index`, `vehicle_reference`).
   - **Row Count:** 937,265 records.
   - **Key Attributes:** Vehicle type (pedal cycle, motorcycle, car, bus, goods, HGV, mobility scooter, personal powered transporter, ridden horse), driver demographics (age, sex), vehicle age, engine capacity, manoeuvre, impact point, towing, skidding.
   - **Relationship:** Many-to-one relationship with collisions (100% link rate to valid collision records).

3. **Casualties (`dft-road-casualty-statistics-casualty-last-5-years.csv`):**
   - **Grain:** 1 row per casualty resulting from a collision (`collision_index`, `casualty_reference`).
   - **Row Count:** 652,821 records.
   - **Key Attributes:** Casualty severity (Fatal, Serious, Slight), casualty class (driver/rider, passenger, pedestrian), casualty age, casualty sex, pedestrian movement, casualty type.
   - **Relationship:** Many-to-one relationship with collisions (100% link rate to valid collision records).

---

## 2. Geographic Identifiers and Coverage (2021–2025)

Analysis of the 513,801 official collision records across 2021–2025 reveals distinct coverage characteristics among geographic identifier fields:

| Field Name | Data Type | Coverage Rate | Status & Recommendation |
| :--- | :--- | :--- | :--- |
| `local_authority_ons_district` | String (9-char GSS) | **100.00%** (513,801 / 513,801) | **Primary District Identifier**: Validated ONS district code (e.g. `E09000001`). Recommended for all district-level aggregations and spatial joins. |
| `local_authority_highway_current` | String (9-char GSS) | **99.99%** (513,748 / 513,801) | **Primary Highway Authority**: Reflects current administrative highway responsibility boundaries. |
| `police_force` | Integer | **100.00%** (513,801 / 513,801) | Police force area identifier. Recommended for regional and institutional reporting. |
| `latitude` / `longitude` | Double | **99.99%** (513,748 / 513,801) | Only 53 records missing coordinates. Recommended for spatial GIS mapping and distance calculations. |
| `lsoa_of_accident_location` | String (9-char GSS) | **95.99%** (493,178 / 513,801) | Lower Layer Super Output Area. Recommended for socioeconomic (IMD) decile linkage. |
| `local_authority_district` | Integer | **0.04%** (194 / 513,801) | **Deprecated / Obsolete**: 99.96% missing (`-1`). Contains zero valid records for 2022–2025. Must **not** be used for area-level reporting. |

---

## 3. Data Quality, Sentinel Values, and Limitations

### Sentinel Handling Principle
In accordance with official DfT STATS19 data definitions:
- The sentinel code **`-1`** denotes `"Data missing or out of range"` or `"Unallocated"`.
- Other sentinel codes include `99` / `9` for `"Unknown"` across specific categorical dimensions.
- Sentinel values are **never** converted to zero or arbitrarily imputed during ingestion.
- The pipeline preserves raw integer codes in raw/staging views while providing clean, typed nullable columns (e.g. `speed_limit_mph` is `NULL` when raw `speed_limit = -1`) and human-readable descriptive labels in the analytical marts.

### STATS19 Reporting Scope and Known Limitations
- **Personal Injury Only:** STATS19 records only collisions that involve personal injury and are reported to police. Damage-only collisions are not recorded.
- **Reporting Bias:** Slight injuries and collisions involving single pedal cyclists have a lower reporting rate compared to fatal and serious collisions.
- **Reporting Standard Changes:** Injury-based reporting (CRASH system) adoption across police forces has refined the categorization between Serious and Slight injuries since 2017.
