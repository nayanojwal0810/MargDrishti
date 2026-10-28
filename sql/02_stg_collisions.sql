-- 02_stg_collisions.sql
-- Cleaned, typed collision staging view with human-readable labels,
-- rigorous severity classification, clean missing-time handling, and explicit sentinel codes.

CREATE OR REPLACE VIEW stg_collisions AS
SELECT
    CAST(collision_index AS VARCHAR) AS collision_index,
    collision_year,
    CAST(collision_ref_no AS VARCHAR) AS collision_ref_no,
    
    -- Temporal attributes (preserves date when valid, sets timestamp/hour to NULL if time is missing/invalid)
    TRY_CAST(date AS DATE) AS collision_date,
    TRY_CAST(time AS TIME) AS collision_time,
    CASE
        WHEN TRY_CAST(date AS DATE) IS NOT NULL AND TRY_CAST(time AS TIME) IS NOT NULL
        THEN date_trunc('hour', TRY_CAST(date AS DATE) + TRY_CAST(time AS TIME))
        ELSE NULL
    END AS collision_timestamp,
    EXTRACT(YEAR FROM TRY_CAST(date AS DATE)) AS derived_year,
    EXTRACT(MONTH FROM TRY_CAST(date AS DATE)) AS collision_month,
    CASE
        WHEN TRY_CAST(time AS TIME) IS NOT NULL
        THEN EXTRACT(HOUR FROM TRY_CAST(time AS TIME))
        ELSE NULL
    END AS collision_hour,
    day_of_week,
    CASE day_of_week
        WHEN 1 THEN 'Sunday'
        WHEN 2 THEN 'Monday'
        WHEN 3 THEN 'Tuesday'
        WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday'
        WHEN 6 THEN 'Friday'
        WHEN 7 THEN 'Saturday'
        ELSE 'Unknown'
    END AS day_of_week_name,
    CASE WHEN day_of_week IN (1, 7) THEN 1 ELSE 0 END AS is_weekend,
    
    -- Collision Severity & Binary Target (strictly maps 1/2 to 1, 3 to 0, and unexpected codes to NULL)
    collision_severity,
    CASE collision_severity
        WHEN 1 THEN 'Fatal'
        WHEN 2 THEN 'Serious'
        WHEN 3 THEN 'Slight'
        ELSE NULL
    END AS collision_severity_name,
    CASE
        WHEN collision_severity IN (1, 2) THEN 1
        WHEN collision_severity = 3 THEN 0
        ELSE NULL
    END AS is_fatal_or_serious, -- Binary KSI target: 1=Fatal/Serious, 0=Slight, NULL=Unknown/Invalid
    
    -- Road environment & geometry
    first_road_class,
    CASE first_road_class
        WHEN 1 THEN 'Motorway'
        WHEN 2 THEN 'A(M)'
        WHEN 3 THEN 'A'
        WHEN 4 THEN 'B'
        WHEN 5 THEN 'C'
        WHEN 6 THEN 'Unclassified'
        ELSE 'Unknown'
    END AS first_road_class_name,
    first_road_number,
    
    road_type,
    CASE road_type
        WHEN 1 THEN 'Roundabout'
        WHEN 2 THEN 'One way street'
        WHEN 3 THEN 'Dual carriageway'
        WHEN 6 THEN 'Single carriageway'
        WHEN 7 THEN 'Slip road'
        WHEN 9 THEN 'Unknown'
        WHEN -1 THEN 'Missing / Out of range'
        ELSE 'Other'
    END AS road_type_name,
    
    speed_limit,
    CASE WHEN speed_limit = -1 THEN NULL ELSE speed_limit END AS speed_limit_mph,
    
    junction_detail,
    junction_control,
    CASE junction_control
        WHEN 1 THEN 'Authorised person'
        WHEN 2 THEN 'Auto traffic signal'
        WHEN 3 THEN 'Stop sign'
        WHEN 4 THEN 'Give way or uncontrolled'
        WHEN -1 THEN 'Missing / Uncontrolled'
        ELSE 'Unknown'
    END AS junction_control_name,
    
    -- Environmental conditions
    light_conditions,
    CASE light_conditions
        WHEN 1 THEN 'Daylight'
        WHEN 4 THEN 'Darkness - lights lit'
        WHEN 5 THEN 'Darkness - lights unlit'
        WHEN 6 THEN 'Darkness - no lights'
        WHEN 7 THEN 'Darkness - lighting unknown'
        WHEN -1 THEN 'Missing / Out of range'
        ELSE 'Other'
    END AS light_conditions_name,
    
    weather_conditions,
    CASE weather_conditions
        WHEN 1 THEN 'Fine no high winds'
        WHEN 2 THEN 'Raining no high winds'
        WHEN 3 THEN 'Snowing no high winds'
        WHEN 4 THEN 'Fine + high winds'
        WHEN 5 THEN 'Raining + high winds'
        WHEN 6 THEN 'Snowing + high winds'
        WHEN 7 THEN 'Fog or mist'
        WHEN 8 THEN 'Other'
        WHEN 9 THEN 'Unknown'
        WHEN -1 THEN 'Missing / Out of range'
        ELSE 'Other'
    END AS weather_conditions_name,
    
    road_surface_conditions,
    CASE road_surface_conditions
        WHEN 1 THEN 'Dry'
        WHEN 2 THEN 'Wet or damp'
        WHEN 3 THEN 'Snow'
        WHEN 4 THEN 'Frost or ice'
        WHEN 5 THEN 'Flood 3cm or deeper'
        WHEN 6 THEN 'Oil or diesel'
        WHEN 7 THEN 'Mud'
        WHEN 9 THEN 'Unknown'
        WHEN -1 THEN 'Missing / Out of range'
        ELSE 'Other'
    END AS road_surface_conditions_name,
    
    urban_or_rural_area,
    CASE urban_or_rural_area
        WHEN 1 THEN 'Urban'
        WHEN 2 THEN 'Rural'
        WHEN 3 THEN 'Unallocated'
        ELSE 'Unknown'
    END AS urban_or_rural_area_name,
    
    -- Geographic identifiers & coordinates
    latitude,
    longitude,
    location_easting_osgr,
    location_northing_osgr,
    police_force,
    local_authority_district, -- Deprecated legacy numeric field (99.96% unallocated in 2021-2025)
    local_authority_ons_district, -- Primary official ONS 9-character district identifier (100% valid coverage)
    local_authority_highway,
    local_authority_highway_current, -- Primary official current highway authority code (99.99% valid coverage)
    lsoa_of_accident_location,
    
    -- Raw recorded counts (scene census)
    number_of_vehicles AS recorded_number_of_vehicles,
    number_of_casualties AS recorded_number_of_casualties,
    
    -- Post-crash response indicators (isolated for quality audit, NOT for predictive features)
    did_police_officer_attend_scene_of_accident,
    enhanced_severity_collision,
    collision_injury_based

FROM raw_collisions;
