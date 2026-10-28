-- 03_agg_vehicle_summary.sql
-- Aggregates vehicle-level data strictly to the collision grain (1 row per collision).
-- All vehicle-type codes match the official DfT STATS19 / STATS20 specification.

CREATE OR REPLACE TABLE agg_vehicle_summary AS
SELECT
    CAST(collision_index AS VARCHAR) AS collision_index,
    
    -- Total count of vehicles involved
    COUNT(*) AS total_vehicles_in_dataset,
    
    -- Specific vehicle type counts (verified against official STATS19 specification)
    COUNT(CASE WHEN vehicle_type = 1 THEN 1 END) AS pedal_cycle_count,
    COUNT(CASE WHEN vehicle_type IN (2, 3, 4, 5, 23, 97) THEN 1 END) AS motorcycle_count,
    COUNT(CASE WHEN vehicle_type = 23 THEN 1 END) AS electric_motorcycle_count,
    COUNT(CASE WHEN vehicle_type IN (8, 9) THEN 1 END) AS car_taxi_count,
    COUNT(CASE WHEN vehicle_type IN (10, 11) THEN 1 END) AS bus_coach_count,
    COUNT(CASE WHEN vehicle_type = 19 THEN 1 END) AS van_lgv_count,
    COUNT(CASE WHEN vehicle_type IN (20, 21) THEN 1 END) AS hgv_count,
    COUNT(CASE WHEN vehicle_type IN (19, 20, 21, 98) THEN 1 END) AS goods_vehicle_count,
    COUNT(CASE WHEN vehicle_type = 16 THEN 1 END) AS ridden_horse_count, -- Code 16 is Ridden horse (not pedal cycle)
    COUNT(CASE WHEN vehicle_type = 17 THEN 1 END) AS agricultural_vehicle_count,
    COUNT(CASE WHEN vehicle_type = 22 THEN 1 END) AS mobility_scooter_count,
    COUNT(CASE WHEN vehicle_type = 33 OR escooter_flag = 1 THEN 1 END) AS personal_transporter_count, -- PLEVs & e-scooters
    COUNT(CASE WHEN vehicle_type = 90 THEN 1 END) AS other_vehicle_count,
    COUNT(CASE WHEN vehicle_type IN (-1, 99) THEN 1 END) AS unknown_vehicle_type_count,
    
    -- Presence flags (0 or 1)
    MAX(CASE WHEN vehicle_type = 1 THEN 1 ELSE 0 END) AS has_pedal_cycle,
    MAX(CASE WHEN vehicle_type IN (2, 3, 4, 5, 23, 97) THEN 1 ELSE 0 END) AS has_motorcycle,
    MAX(CASE WHEN vehicle_type = 23 THEN 1 ELSE 0 END) AS has_electric_motorcycle,
    MAX(CASE WHEN vehicle_type IN (8, 9) THEN 1 ELSE 0 END) AS has_car_taxi,
    MAX(CASE WHEN vehicle_type IN (10, 11) THEN 1 ELSE 0 END) AS has_bus_coach,
    MAX(CASE WHEN vehicle_type = 19 THEN 1 ELSE 0 END) AS has_van_lgv,
    MAX(CASE WHEN vehicle_type IN (20, 21) THEN 1 ELSE 0 END) AS has_hgv,
    MAX(CASE WHEN vehicle_type IN (19, 20, 21, 98) THEN 1 ELSE 0 END) AS has_goods_vehicle,
    MAX(CASE WHEN vehicle_type = 16 THEN 1 ELSE 0 END) AS has_ridden_horse,
    MAX(CASE WHEN vehicle_type = 17 THEN 1 ELSE 0 END) AS has_agricultural_vehicle,
    MAX(CASE WHEN vehicle_type = 22 THEN 1 ELSE 0 END) AS has_mobility_scooter,
    MAX(CASE WHEN vehicle_type = 33 OR escooter_flag = 1 THEN 1 ELSE 0 END) AS has_personal_transporter,
    MAX(CASE WHEN vehicle_type IN (-1, 99) THEN 1 ELSE 0 END) AS has_unknown_vehicle_type,
    
    -- Vulnerable road user vehicle involvement (pedal cycles, motorcycles, ridden horses, mobility scooters, PLEVs/e-scooters)
    MAX(CASE WHEN vehicle_type IN (1, 2, 3, 4, 5, 16, 22, 23, 33, 97) OR escooter_flag = 1 THEN 1 ELSE 0 END) AS has_vulnerable_road_user_vehicle,
    
    -- Driver demographic aggregations (ignoring sentinel -1 / unknown values)
    MIN(CASE WHEN age_of_driver > 0 THEN age_of_driver END) AS youngest_driver_age,
    MAX(CASE WHEN age_of_driver > 0 THEN age_of_driver END) AS oldest_driver_age,
    AVG(CASE WHEN age_of_driver > 0 THEN age_of_driver END) AS avg_driver_age,
    MAX(CASE WHEN age_of_driver BETWEEN 17 AND 24 THEN 1 ELSE 0 END) AS has_young_driver,
    MAX(CASE WHEN age_of_driver >= 70 THEN 1 ELSE 0 END) AS has_older_driver,
    MAX(CASE WHEN sex_of_driver = 1 THEN 1 ELSE 0 END) AS has_male_driver,
    MAX(CASE WHEN sex_of_driver = 2 THEN 1 ELSE 0 END) AS has_female_driver,
    
    -- Vehicle age & engine characteristics (ignoring sentinel -1 / unknown values)
    MIN(CASE WHEN age_of_vehicle >= 0 THEN age_of_vehicle END) AS newest_vehicle_age,
    MAX(CASE WHEN age_of_vehicle >= 0 THEN age_of_vehicle END) AS oldest_vehicle_age,
    AVG(CASE WHEN age_of_vehicle >= 0 THEN age_of_vehicle END) AS avg_vehicle_age,
    MAX(CASE WHEN engine_capacity_cc > 0 THEN engine_capacity_cc END) AS max_engine_capacity_cc,
    
    -- Dynamic incident collision-context and event variables (manoeuvres, skidding, objects hit)
    -- NOTE: These are collision-context variables; feature eligibility must be reviewed before future model training.
    MAX(CASE WHEN towing_and_articulation > 0 THEN 1 ELSE 0 END) AS has_towing_or_articulation,
    MAX(CASE WHEN skidding_and_overturning > 0 THEN 1 ELSE 0 END) AS has_skidding_or_overturning,
    MAX(CASE WHEN vehicle_leaving_carriageway > 0 THEN 1 ELSE 0 END) AS has_vehicle_leaving_carriageway,
    MAX(CASE WHEN hit_object_in_carriageway > 0 THEN 1 ELSE 0 END) AS has_hit_object_in_carriageway,
    MAX(CASE WHEN hit_object_off_carriageway > 0 THEN 1 ELSE 0 END) AS has_hit_object_off_carriageway

FROM raw_vehicles
GROUP BY collision_index;
