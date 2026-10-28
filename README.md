# MargDrishti

**Road Safety Analytics & Risk-Adjusted Severity Benchmarking**

MargDrishti is an end-to-end road safety analytics project that turns UK collision records into reliable data, clear business measures, and evidence that supports further investigation. It combines analytics engineering, SQL, statistical analysis, and a supporting traditional machine-learning workflow.

## Project goals

- Build a reliable and repeatable pipeline for UK road-safety data.
- Create well-defined analytical tables and quality checks.
- Understand how collision patterns and serious outcomes vary over time, road conditions, and areas where location data is reliable.
- Reproduce and evaluate established traditional ML models for collision-severity analysis.
- Assess whether calibrated model estimates can support fair observed-versus-expected comparisons.
- Present the findings clearly for analysts and decision-makers.

## What the project includes

### Data engineering and analytics

Ingest and validate the source files, document data definitions, handle unknown values carefully, and create reusable analytical tables. SQL will support the main metrics and reporting logic.

### Business and statistical analysis

Explore collision counts, fatal-or-serious collision burden, severity shares, trends, and differences across recorded conditions. Keep collision-level and casualty-level measures separate.

### Machine learning and evaluation

Use established traditional ML approaches as a reference. Evaluate them with a clean training, validation, and test design. Check probability calibration and uncertainty before using model estimates for area-level benchmarking.

### Reporting

Power BI will present the validated analytical results in a clear, interactive report. The dashboard design will use consistent navigation, readable KPI cards, focused charts, and useful filters. Its final pages and visuals will follow the questions the data can answer reliably.

## Technology

- Python and pandas
- SQL and DuckDB
- Parquet
- scikit-learn and traditional tree-based models
- Microsoft Power BI and DAX
- pytest

## Data sources

The project uses UK Department for Transport road-safety records and a published research dataset. The implementation will document source links, coverage, definitions, and limitations.

## Responsible interpretation

The model estimates the severity outcome of a reported collision. It does not predict where a future collision will occur or establish causation. Area comparisons depend on valid geographic identifiers, suitable model calibration, and uncertainty estimates. Results will be described as associations and risk-adjusted comparisons, not proof that a road feature caused an outcome.

## Project status

The project is under development. Results, screenshots, and instructions will be added after the related work has been implemented and checked.
