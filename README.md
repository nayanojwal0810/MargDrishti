# MargDrishti

**Road Safety Analytics & Risk-Adjusted Severity Benchmarking**

An end-to-end road safety analytics platform that combines SQL-based data modelling, statistical analysis, and traditional machine learning to explore collision severity patterns across the UK. It includes interactive Power BI dashboards, risk-adjusted comparisons, and data-driven insights to support road safety investigation.

## Project overview

MargDrishti turns UK road-safety records into reliable analytical datasets, useful performance measures, and an interactive Power BI experience. It examines trends in reported collisions and serious outcomes, compares patterns across areas and road conditions, and evaluates whether a carefully validated model can support risk-adjusted benchmarking.

## Dashboard

The Power BI report will use a multi-page layout with consistent navigation and focused analysis pages, inspired by professional business intelligence reports.

- **Home:** Project purpose and page navigation.
- **Overview:** Key road-safety measures and trends over time.
- **Collision Patterns:** Severity by road, lighting, weather, junction and time conditions.
- **Area Comparison:** Compare collision burden and severity measures across areas with valid geographic data.
- **Risk-Adjusted Benchmarking:** Compare observed and model-expected serious outcomes, with uncertainty and sample-size context where the methodology supports it.
- **Model & Data Quality:** Evaluation results, calibration, feature interpretation, and data-quality checks.

## Technology

- Python and pandas
- SQL and DuckDB
- Parquet
- scikit-learn and traditional tree-based machine learning
- Microsoft Power BI and DAX
- pytest

## Data

The project uses UK Department for Transport road-safety records and a published research dataset. Data definitions, coverage, limitations, and source acknowledgements will be documented alongside the implementation.

## Project status

The project is under development. Findings, evaluation results, and dashboard screenshots will be added after the related analysis and implementation have been checked.

## Responsible interpretation

The model estimates the severity outcome of a reported collision; it does not predict where a future collision will occur or establish causation. Area comparisons depend on data quality, valid area identifiers, probability calibration, and uncertainty. Results will be described as associations and risk-adjusted comparisons, not proof that a road feature caused an outcome.
