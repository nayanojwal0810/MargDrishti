-- 04_agg_casualty_summary.sql
-- Aggregates casualty records to the collision grain (1 row per collision).
-- All casualty codes match official DfT STATS19 specifications.
-- NOTE: Casualty outcomes are post-crash consequences. This table is reserved for
-- outcome reporting and statistical burden analysis, NOT for model predictor features.

CREATE OR REPLACE TABLE agg_casualty_summary AS
SELECT
    CAST(collision_index AS VARCHAR) AS collision_index,
    
    -- Severity breakdown
    COUNT(*) AS total_casualties_in_dataset,
    COUNT(CASE WHEN casualty_severity = 1 THEN 1 END) AS fatal_casualty_count,
    COUNT(CASE WHEN casualty_severity = 2 THEN 1 END) AS serious_casualty_count,
    COUNT(CASE WHEN casualty_severity = 3 THEN 1 END) AS slight_casualty_count,
    COUNT(CASE WHEN casualty_severity IN (1, 2) THEN 1 END) AS ksi_casualty_count,
    
    -- Binary severity outcome flags
    MAX(CASE WHEN casualty_severity = 1 THEN 1 ELSE 0 END) AS has_fatal_casualty,
    MAX(CASE WHEN casualty_severity = 2 THEN 1 ELSE 0 END) AS has_serious_casualty,
    MAX(CASE WHEN casualty_severity IN (1, 2) THEN 1 ELSE 0 END) AS has_ksi_casualty,
    
    -- Casualty role breakdown (by casualty_class)
    COUNT(CASE WHEN casualty_class = 1 THEN 1 END) AS driver_rider_casualty_count,
    COUNT(CASE WHEN casualty_class = 2 THEN 1 END) AS passenger_casualty_count,
    COUNT(CASE WHEN casualty_class = 3 OR casualty_type = 0 THEN 1 END) AS pedestrian_casualty_count,
    
    -- Casualty type breakdown (by casualty_type specification)
    COUNT(CASE WHEN casualty_type = 1 THEN 1 END) AS cyclist_casualty_count,
    COUNT(CASE WHEN casualty_type IN (2, 3, 4, 5, 23, 97) THEN 1 END) AS motorcyclist_casualty_count,
    COUNT(CASE WHEN casualty_type IN (8, 9) THEN 1 END) AS car_occupant_casualty_count,
    COUNT(CASE WHEN casualty_type IN (10, 11) THEN 1 END) AS bus_coach_casualty_count,
    COUNT(CASE WHEN casualty_type IN (19, 20, 21, 98) THEN 1 END) AS goods_vehicle_casualty_count,
    COUNT(CASE WHEN casualty_type = 22 THEN 1 END) AS mobility_scooter_casualty_count,
    COUNT(CASE WHEN casualty_type = 33 OR escooter_flag = 1 THEN 1 END) AS personal_transporter_casualty_count,
    COUNT(CASE WHEN casualty_type = 16 THEN 1 END) AS horse_rider_casualty_count,
    
    -- Vulnerable road user casualty flag (pedestrians, cyclists, motorcyclists, horse riders, mobility scooters, PLEVs/e-scooters)
    MAX(CASE WHEN casualty_class = 3 OR casualty_type IN (0, 1, 2, 3, 4, 5, 16, 22, 23, 33, 97) OR escooter_flag = 1 THEN 1 ELSE 0 END) AS has_vulnerable_user_casualty,
    
    -- Age demographic outcomes (ignoring sentinel -1 / unknown values)
    MIN(CASE WHEN age_of_casualty >= 0 THEN age_of_casualty END) AS youngest_casualty_age,
    MAX(CASE WHEN age_of_casualty >= 0 THEN age_of_casualty END) AS oldest_casualty_age,
    COUNT(CASE WHEN age_of_casualty >= 0 AND age_of_casualty < 16 THEN 1 END) AS child_casualty_count,
    COUNT(CASE WHEN age_of_casualty >= 65 THEN 1 END) AS elderly_casualty_count

FROM raw_casualties
GROUP BY collision_index;
