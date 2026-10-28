-- 05_marts.sql
-- Analytical data marts combining validated dimensions and aggregations.
-- Guarantees exact 1:1 collision grain without record duplication.

-- Mart 1: Pre-crash collision and vehicle analytical mart
-- Strictly excludes casualty outcomes to avoid post-crash leakage.
CREATE OR REPLACE TABLE mart_collision_analytical AS
SELECT
    c.collision_index,
    c.collision_year,
    c.collision_ref_no,
    c.collision_date,
    c.collision_time,
    c.collision_timestamp,
    c.derived_year,
    c.collision_month,
    c.collision_hour,
    c.day_of_week,
    c.day_of_week_name,
    c.is_weekend,
    
    -- Severity classification & binary KSI target
    c.collision_severity,
    c.collision_severity_name,
    c.is_fatal_or_serious,
    
    -- Road geometry & speed limits
    c.first_road_class,
    c.first_road_class_name,
    c.first_road_number,
    c.road_type,
    c.road_type_name,
    c.speed_limit,
    c.speed_limit_mph,
    c.junction_detail,
    c.junction_control,
    c.junction_control_name,
    
    -- Environmental conditions
    c.light_conditions,
    c.light_conditions_name,
    c.weather_conditions,
    c.weather_conditions_name,
    c.road_surface_conditions,
    c.road_surface_conditions_name,
    c.urban_or_rural_area,
    c.urban_or_rural_area_name,
    
    -- Location & geographic identifiers
    c.latitude,
    c.longitude,
    c.location_easting_osgr,
    c.location_northing_osgr,
    c.police_force,
    c.local_authority_district,
    c.local_authority_ons_district, -- Primary validated district code (100% coverage)
    c.local_authority_highway,
    c.local_authority_highway_current, -- Primary current highway authority (99.99% coverage)
    c.lsoa_of_accident_location,
    
    -- Aggregated vehicle attributes (1:1 from agg_vehicle_summary)
    COALESCE(v.total_vehicles_in_dataset, c.recorded_number_of_vehicles) AS total_vehicles,
    COALESCE(v.pedal_cycle_count, 0) AS pedal_cycle_count,
    COALESCE(v.motorcycle_count, 0) AS motorcycle_count,
    COALESCE(v.electric_motorcycle_count, 0) AS electric_motorcycle_count,
    COALESCE(v.car_taxi_count, 0) AS car_taxi_count,
    COALESCE(v.bus_coach_count, 0) AS bus_coach_count,
    COALESCE(v.van_lgv_count, 0) AS van_lgv_count,
    COALESCE(v.hgv_count, 0) AS hgv_count,
    COALESCE(v.goods_vehicle_count, 0) AS goods_vehicle_count,
    COALESCE(v.ridden_horse_count, 0) AS ridden_horse_count,
    COALESCE(v.agricultural_vehicle_count, 0) AS agricultural_vehicle_count,
    COALESCE(v.mobility_scooter_count, 0) AS mobility_scooter_count,
    COALESCE(v.personal_transporter_count, 0) AS personal_transporter_count,
    COALESCE(v.other_vehicle_count, 0) AS other_vehicle_count,
    COALESCE(v.unknown_vehicle_type_count, 0) AS unknown_vehicle_type_count,
    
    COALESCE(v.has_pedal_cycle, 0) AS has_pedal_cycle,
    COALESCE(v.has_motorcycle, 0) AS has_motorcycle,
    COALESCE(v.has_electric_motorcycle, 0) AS has_electric_motorcycle,
    COALESCE(v.has_car_taxi, 0) AS has_car_taxi,
    COALESCE(v.has_bus_coach, 0) AS has_bus_coach,
    COALESCE(v.has_van_lgv, 0) AS has_van_lgv,
    COALESCE(v.has_hgv, 0) AS has_hgv,
    COALESCE(v.has_goods_vehicle, 0) AS has_goods_vehicle,
    COALESCE(v.has_ridden_horse, 0) AS has_ridden_horse,
    COALESCE(v.has_agricultural_vehicle, 0) AS has_agricultural_vehicle,
    COALESCE(v.has_mobility_scooter, 0) AS has_mobility_scooter,
    COALESCE(v.has_personal_transporter, 0) AS has_personal_transporter,
    COALESCE(v.has_unknown_vehicle_type, 0) AS has_unknown_vehicle_type,
    COALESCE(v.has_vulnerable_road_user_vehicle, 0) AS has_vulnerable_road_user_vehicle,
    
    v.youngest_driver_age,
    v.oldest_driver_age,
    v.avg_driver_age,
    COALESCE(v.has_young_driver, 0) AS has_young_driver,
    COALESCE(v.has_older_driver, 0) AS has_older_driver,
    COALESCE(v.has_male_driver, 0) AS has_male_driver,
    COALESCE(v.has_female_driver, 0) AS has_female_driver,
    
    v.newest_vehicle_age,
    v.oldest_vehicle_age,
    v.avg_vehicle_age,
    v.max_engine_capacity_cc,
    
    COALESCE(v.has_towing_or_articulation, 0) AS has_towing_or_articulation,
    COALESCE(v.has_skidding_or_overturning, 0) AS has_skidding_or_overturning,
    COALESCE(v.has_vehicle_leaving_carriageway, 0) AS has_vehicle_leaving_carriageway,
    COALESCE(v.has_hit_object_in_carriageway, 0) AS has_hit_object_in_carriageway,
    COALESCE(v.has_hit_object_off_carriageway, 0) AS has_hit_object_off_carriageway

FROM stg_collisions c
LEFT JOIN agg_vehicle_summary v ON c.collision_index = v.collision_index;


-- Mart 2: Collision outcomes and casualty impact mart
-- Dedicated for reporting and injury severity analysis.
CREATE OR REPLACE TABLE mart_collision_outcomes AS
SELECT
    c.collision_index,
    c.collision_year,
    c.collision_date,
    c.collision_severity,
    c.collision_severity_name,
    c.is_fatal_or_serious,
    c.police_force,
    c.local_authority_ons_district,
    c.local_authority_highway_current,
    c.urban_or_rural_area_name,
    
    -- Casualty metrics (1:1 from agg_casualty_summary)
    COALESCE(k.total_casualties_in_dataset, c.recorded_number_of_casualties) AS total_casualties,
    COALESCE(k.fatal_casualty_count, 0) AS fatal_casualty_count,
    COALESCE(k.serious_casualty_count, 0) AS serious_casualty_count,
    COALESCE(k.slight_casualty_count, 0) AS slight_casualty_count,
    COALESCE(k.ksi_casualty_count, 0) AS ksi_casualty_count,
    COALESCE(k.has_fatal_casualty, 0) AS has_fatal_casualty,
    COALESCE(k.has_serious_casualty, 0) AS has_serious_casualty,
    COALESCE(k.has_ksi_casualty, 0) AS has_ksi_casualty,
    
    COALESCE(k.driver_rider_casualty_count, 0) AS driver_rider_casualty_count,
    COALESCE(k.passenger_casualty_count, 0) AS passenger_casualty_count,
    COALESCE(k.pedestrian_casualty_count, 0) AS pedestrian_casualty_count,
    COALESCE(k.cyclist_casualty_count, 0) AS cyclist_casualty_count,
    COALESCE(k.motorcyclist_casualty_count, 0) AS motorcyclist_casualty_count,
    COALESCE(k.car_occupant_casualty_count, 0) AS car_occupant_casualty_count,
    COALESCE(k.bus_coach_casualty_count, 0) AS bus_coach_casualty_count,
    COALESCE(k.goods_vehicle_casualty_count, 0) AS goods_vehicle_casualty_count,
    COALESCE(k.mobility_scooter_casualty_count, 0) AS mobility_scooter_casualty_count,
    COALESCE(k.personal_transporter_casualty_count, 0) AS personal_transporter_casualty_count,
    COALESCE(k.horse_rider_casualty_count, 0) AS horse_rider_casualty_count,
    COALESCE(k.has_vulnerable_user_casualty, 0) AS has_vulnerable_user_casualty,
    
    k.youngest_casualty_age,
    k.oldest_casualty_age,
    COALESCE(k.child_casualty_count, 0) AS child_casualty_count,
    COALESCE(k.elderly_casualty_count, 0) AS elderly_casualty_count

FROM stg_collisions c
LEFT JOIN agg_casualty_summary k ON c.collision_index = k.collision_index;
