-- 06_analytics_views.sql
-- Descriptive analytics layer built on top of mart_collision_analytical.
-- Provides aggregated severity profiles by year, road context dimensions, and vehicle involvement.

-- View 1: Yearly Collision Severity Profile
CREATE OR REPLACE VIEW analytics_yearly_severity AS
SELECT
    collision_year,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY collision_year
ORDER BY collision_year;


-- View 2: Collision Severity by Road Context Dimensions (Long Form)
CREATE OR REPLACE VIEW analytics_severity_by_road_context AS
-- Dimension 1: road_type
SELECT
    'road_type' AS dimension_name,
    CAST(road_type AS VARCHAR) AS dimension_code,
    COALESCE(road_type_name, 'Missing / Out of range') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY road_type, road_type_name

UNION ALL

-- Dimension 2: speed_limit
SELECT
    'speed_limit' AS dimension_name,
    CAST(speed_limit AS VARCHAR) AS dimension_code,
    CASE
        WHEN speed_limit = -1 OR speed_limit IS NULL THEN 'Missing / Out of range'
        ELSE CAST(speed_limit AS VARCHAR) || ' mph'
    END AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY speed_limit

UNION ALL

-- Dimension 3: junction_control
SELECT
    'junction_control' AS dimension_name,
    CAST(junction_control AS VARCHAR) AS dimension_code,
    COALESCE(junction_control_name, 'Missing / Out of range') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY junction_control, junction_control_name

UNION ALL

-- Dimension 4: light_conditions
SELECT
    'light_conditions' AS dimension_name,
    CAST(light_conditions AS VARCHAR) AS dimension_code,
    COALESCE(light_conditions_name, 'Missing / Out of range') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY light_conditions, light_conditions_name

UNION ALL

-- Dimension 5: weather_conditions
SELECT
    'weather_conditions' AS dimension_name,
    CAST(weather_conditions AS VARCHAR) AS dimension_code,
    COALESCE(weather_conditions_name, 'Missing / Out of range') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY weather_conditions, weather_conditions_name

UNION ALL

-- Dimension 6: road_surface_conditions
SELECT
    'road_surface_conditions' AS dimension_name,
    CAST(road_surface_conditions AS VARCHAR) AS dimension_code,
    COALESCE(road_surface_conditions_name, 'Missing / Out of range') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY road_surface_conditions, road_surface_conditions_name

UNION ALL

-- Dimension 7: urban_or_rural_area
SELECT
    'urban_or_rural_area' AS dimension_name,
    CAST(urban_or_rural_area AS VARCHAR) AS dimension_code,
    COALESCE(urban_or_rural_area_name, 'Unknown') AS dimension_label,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
GROUP BY urban_or_rural_area, urban_or_rural_area_name;


-- View 3: Collision Severity by Vehicle Involvement Group
-- Note: Vehicle groups can overlap; a single multi-vehicle collision may involve multiple groups.
-- Each row represents an independent group comparison; counts across groups must not be summed together.
CREATE OR REPLACE VIEW analytics_severity_by_vehicle_involvement AS
SELECT
    'pedal_cycle' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_pedal_cycle = 1

UNION ALL

SELECT
    'motorcycle' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_motorcycle = 1

UNION ALL

SELECT
    'car_taxi' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_car_taxi = 1

UNION ALL

SELECT
    'bus_coach' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_bus_coach = 1

UNION ALL

SELECT
    'van_lgv' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_van_lgv = 1

UNION ALL

SELECT
    'hgv' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_hgv = 1

UNION ALL

SELECT
    'mobility_scooter' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_mobility_scooter = 1

UNION ALL

SELECT
    'personal_transporter' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_personal_transporter = 1

UNION ALL

SELECT
    'vulnerable_road_user_vehicle' AS vehicle_group,
    COUNT(*) AS collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END) AS known_severity_collision_count,
    COUNT(CASE WHEN collision_severity = 1 THEN 1 END) AS fatal_collision_count,
    COUNT(CASE WHEN collision_severity = 2 THEN 1 END) AS serious_collision_count,
    COUNT(CASE WHEN collision_severity = 3 THEN 1 END) AS slight_collision_count,
    COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS ksi_collision_count,
    COUNT(CASE WHEN collision_severity IS NULL OR collision_severity NOT IN (1, 2, 3) THEN 1 END) AS missing_or_invalid_severity_count,
    ROUND(
        CAST(COUNT(CASE WHEN collision_severity IN (1, 2) THEN 1 END) AS DOUBLE)
        / NULLIF(COUNT(CASE WHEN collision_severity IN (1, 2, 3) THEN 1 END), 0)
        * 100.0,
        2
    ) AS ksi_collision_share_pct
FROM mart_collision_analytical
WHERE has_vulnerable_road_user_vehicle = 1;
