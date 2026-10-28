# Data Sources and Schema Documentation

MargDrishti integrates official UK road-casualty records published by the Department for Transport (DfT) alongside an established open research dataset.

---

## 1. Official STATS19 Road Casualty Statistics

The Department for Transport collects road traffic collision records reported by police forces across Great Britain via the STATS19 reporting system.

- **Source:** [UK Department for Transport - Road Casualty Statistics](https://www.gov.uk/government/collections/road-accidents-and-safety-statistics)
- **Snapshot Period:** 2021–2025 (rolling 5-year official release)
- **Format:** CSV files converted to Apache Parquet
- **Reporting Scope:** Personal injury collisions occurring on public roads in Great Britain resulting in injury or death reported to the police.

### File Descriptions

1. **Collisions (`dft-road-casualty-statistics-collision-last-5-years.csv`):**
   - **Grain:** 1 row per reported collision (`collision_index`).
   - **Row Count:** 513,801 records.
   - **Key Attributes:** Collision date, time, severity (Fatal, Serious, Slight), speed limit, road type, road classification, weather conditions, light conditions, road surface conditions, urban/rural classification, geographic coordinates.

2. **Vehicles (`dft-road-casualty-statistics-vehicle-last-5-years.csv`):**
   - **Grain:** 1 row per vehicle involved in a collision (`collision_index`, `vehicle_reference`).
   - **Row Count:** 937,265 records.
   - **Key Attributes:** Vehicle type (pedal cycle, motorcycle, car, bus, goods, HGV), driver demographics (age, sex), vehicle age, engine capacity, manoeuvre, impact point, towing, skidding.
   - **Relationship:** Many-to-one relationship with collisions (100% link rate to valid collision records).

3. **Casualties (`dft-road-casualty-statistics-casualty-last-5-years.csv`):**
   - **Grain:** 1 row per casualty resulting from a collision (`collision_index`, `casualty_reference`).
   - **Row Count:** 652,821 records.
   - **Key Attributes:** Casualty severity (Fatal, Serious, Slight), casualty class (driver/rider, passenger, pedestrian), casualty age, casualty sex, pedestrian movement.
   - **Relationship:** Many-to-one relationship with collisions (100% link rate to valid collision records).

---

## 2. Research Replication Dataset

- **Source:** PLOS ONE (doi: 10.1371/journal.pone.0347873) supplementary archive / Zenodo (record 19135623).
- **Snapshot Period:** 2020–2024 (503,475 collision records).
- **Format:** RAR archive containing `UKdata.csv`, converted to separate Parquet.
- **Handling Principle:** The research dataset snapshot covers an earlier time window (2020–2024) compared to the current official rolling dataset (2021–2025). The research dataset is kept in an isolated schema/table (`research_collisions_2020_2024`) and is never merged or unioned into the official tables.

---

## 3. Data Quality & Sentinel Values

In accordance with official DfT STATS19 data definitions:

- The sentinel code **`-1`** denotes `"Data missing or out of range"` or `"Unallocated"`.
- Sentinel values are **not** replaced with zero or imputed with arbitrary numbers during ingestion.
- The data pipeline preserves raw integer codes in raw/staging views while providing clean, typed nullable columns (e.g. `speed_limit_mph` is `NULL` when raw `speed_limit = -1`) and human-readable descriptive labels in the analytical marts.
