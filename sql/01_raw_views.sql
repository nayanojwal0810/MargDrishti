-- 01_raw_views.sql
-- Direct views over the converted Parquet files.

CREATE OR REPLACE VIEW raw_collisions AS
SELECT * FROM read_parquet('{parquet_dir}/official_collision_2021_2025.parquet');

CREATE OR REPLACE VIEW raw_vehicles AS
SELECT * FROM read_parquet('{parquet_dir}/official_vehicle_2021_2025.parquet');

CREATE OR REPLACE VIEW raw_casualties AS
SELECT * FROM read_parquet('{parquet_dir}/official_casualty_2021_2025.parquet');
