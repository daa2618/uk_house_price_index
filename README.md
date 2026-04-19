# UK House Price Index Dashboard

![HPI Dashboard landing](docs/screenshots/dashboard_landing.jpg) ![Region selector](docs/screenshots/region_selector.jpg) ![Plot configuration](docs/screenshots/plot_configuration.jpg) ![Interactive plot](docs/screenshots/interactive_plot.jpg)

A Python toolkit and interactive Dash application for exploring the UK House Price Index (HPI) across geographies, time periods, and property characteristics. The project combines data ingestion utilities, caching/versioning helpers, and a gallery of ready-made Plotly visualisations.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Project Layout](#project-layout)
- [Getting Started](#getting-started)
- [Usage](#usage)
  - [Programmatic API](#programmatic-api)
  - [Collecting data in bulk](#collecting-data-in-bulk)
  - [Regenerating the static plot gallery](#regenerating-the-static-plot-gallery)
  - [Launching the dashboard](#launching-the-dashboard)
- [Sample Visual Gallery](#sample-visual-gallery)
- [Notebooks](#notebooks)
- [License](#license)
- [Author](#author)

## Overview

The UK Land Registry publishes the UK House Price Index (HPI) via SPARQL and REST endpoints. This repository wraps those services in a composable data toolkit:

- Ingest and normalise HPI series with a single Python API.
- Persist locally cached datasets for reproducible analysis runs.
- Generate high-quality Plotly figures for reporting.
- Explore insights interactively through a Dash dashboard optimised for quick comparisons across regions, property types, and buyer characteristics.

## Features

- **End-to-end data access**: `HousePriceIndex` (in `ukhpi.core.hpi`) builds SPARQL queries, fetches monthly series, and reshapes them into tidy data frames.
- **Caching and versioning**: `FileVersion` and `Dataset` (in `ukhpi.io`) persist timestamped snapshots under `src/ukhpi/cache/`.
- **Plot factory**: `HousePriceIndexPlots` (in `ukhpi.plotting.hpi_plots`) exposes dozens of pre-configured Plotly figures covering averages, index trends, annual change, and sales volumes.
- **Dash dashboard**: `ukhpi.dashboard.app_improved` ships a polished, themable app with region pickers, year sliders, and tabbed plot collections.
- **Geospatial helpers**: `ukhpi.geo.ops` and `ukhpi.postcode_lookups` simplify mapping and regional filtering workflows.
- **Automated assets**: `scripts/generate_plots.py` regenerates the static chart gallery in batch.

## Project Layout

```text
uk_house_price_index/
├── src/ukhpi/
│   ├── core/                  # SPARQL + HPI fetch/normalise domain
│   │   ├── hpi.py             # HousePriceIndex
│   │   ├── sparql.py          # SparqlQuery
│   │   ├── ppi.py             # Price Paid Data (postcode-level transactions)
│   │   └── collection.py      # Bulk regional collector + CLI (ukhpi-collect)
│   ├── geo/
│   │   └── ops.py             # GeoOps — choropleth + region merging
│   ├── plotting/
│   │   ├── hpi_plots.py       # HousePriceIndexPlots — plot_* factory
│   │   ├── categories.py      # CategoryPlots / BasicPlots / PostProcess
│   │   ├── theme.py           # Plotly theme, colour schemes, shared imports
│   │   └── save.py            # PlotSaver — timestamped image export
│   ├── io/
│   │   ├── versioning.py      # FileVersion — timestamped cache files
│   │   ├── loader.py          # Dataset — read cached CSV/JSON from disk
│   │   └── writer.py          # WriteFile — persist DataFrames
│   ├── dashboard/
│   │   ├── app_improved.py    # Production Dash app (port 8054)
│   │   ├── app_basic.py       # Minimal starter variant
│   │   └── assets/            # Dash auto-loaded CSS/JS
│   ├── postcode_lookups/      # Postcode-level helpers
│   ├── cache/                 # Runtime cache (gitignored)
│   │   ├── hpi_data/          # Per-region HPI CSVs
│   │   ├── region_data/       # Region metadata
│   │   └── geo_data/          # GeoJSON boundaries
│   ├── images/                # Static plot gallery
│   ├── loggers.py             # BasicLogger
│   └── text.py                # String helpers (snake_case, etc.)
├── scripts/collect_data.py    # Thin CLI delegate → ukhpi.core.collection:main
├── tests/                     # pytest suite
├── notebooks/try_hpi.ipynb    # Exploratory notebook
└── docs/screenshots/          # Dashboard screenshots used in this README
```

## Getting Started

Prerequisites:
- Python 3.12+ (per `pyproject.toml`)
- [Poetry](https://python-poetry.org/) recommended

Clone and install:

```bash
git clone https://github.com/daa2618/uk_house_price_index.git
cd uk_house_price_index
poetry install
```

Alternatively, with plain `pip`:

```bash
git clone https://github.com/daa2618/uk_house_price_index.git
cd uk_house_price_index
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .
```

The editable install exposes the package as `ukhpi`.

## Usage

### Programmatic API

```python
from ukhpi.core.hpi import HousePriceIndex
from ukhpi.plotting.hpi_plots import HousePriceIndexPlots

hpi = HousePriceIndex()

# Tidy DataFrame for 2020–2024 West Northamptonshire HPI
df = hpi.fetch_hpi(start_year=2020, end_year=2024, region="west-northamptonshire")

# Pre-built Plotly figures
plots = HousePriceIndexPlots(start_year=2020, end_year=2024, region="west-northamptonshire")
fig = plots.plot_average_price_by_property_types()
fig.show()
```

- Regions are accepted as case-insensitive slugs (spaces become `-`).
- `HousePriceIndexPlots` lazily fetches data on first access and caches under `src/ukhpi/cache/`.
- `fetch_hpi` returns a `pandas.DataFrame` directly. First call hits SPARQL and writes a timestamped CSV; subsequent calls within the same day load the cached file.

### Collecting data in bulk

The bulk collector fetches every region in parallel and writes one CSV per region to the cache:

```bash
poetry run python scripts/collect_data.py --start-year 1990 --end-year 2025
```

Options: `--data-path` (defaults to `src/ukhpi/cache/hpi_data`), `--start-year`, `--end-year`.

### Regenerating the static plot gallery

```bash
poetry run python scripts/generate_plots.py \
    --start-year 2020 --end-year 2024 --region united-kingdom
```

Options: `--start-year`, `--end-year`, `--region`, `--output-dir` (defaults to `src/ukhpi/images/`). Figures are saved via `PlotSaver`.

### Launching the dashboard

The improved Dash application auto-opens a browser tab on port `8054`:

```bash
poetry run python scripts/dashboard_improved.py
```

Options: `--host`, `--port`, `--no-debug`, `--no-open-browser`. Use the region dropdown, metric selectors, and year slider to explore different breakdowns. `scripts/dashboard_basic.py` is a lean alternative or a starting point for custom layouts.

## Sample Visual Gallery

### Average Price Views
![Average Price By Build Types London 2020 2024](src/ukhpi/images/average_price_by_build_types_london_2020_2024.png) ![Average Price By Build Types West-Northamptonshire 2020 2024](src/ukhpi/images/average_price_by_build_types_west-northamptonshire_2020_2024.png)
![Average Price By Occupant Types West-Northamptonshire 2020 2024](src/ukhpi/images/average_price_by_occupant_types_west-northamptonshire_2020_2024.png) ![Average Price By Payment Types West-Northamptonshire 2020 2024](src/ukhpi/images/average_price_by_payment_types_west-northamptonshire_2020_2024.png)
![Average Price By Property Types London 2020 2024](src/ukhpi/images/average_price_by_property_types_london_2020_2024.png) ![Average Price By Property Types West-Northamptonshire 2020 2024](src/ukhpi/images/average_price_by_property_types_west-northamptonshire_2020_2024.png)

### Index Levels
![House Price Index By Build Type London 2020 2024](src/ukhpi/images/house_price_index_by_build_type_london_2020_2024.png) ![House Price Index By Build Type West-Northamptonshire 2020 2024](src/ukhpi/images/house_price_index_by_build_type_west-northamptonshire_2020_2024.png)
![House Price Index By Occupant Types West-Northamptonshire 2020 2024](src/ukhpi/images/house_price_index_by_occupant_types_west-northamptonshire_2020_2024.png) ![House Price Index By Payment Types West-Northamptonshire 2020 2024](src/ukhpi/images/house_price_index_by_payment_types_west-northamptonshire_2020_2024.png)
![House Price Index By Property Types London 2020 2024](src/ukhpi/images/house_price_index_by_property_types_london_2020_2024.png) ![House Price Index By Property Types West-Northamptonshire 2020 2024](src/ukhpi/images/house_price_index_by_property_types_west-northamptonshire_2020_2024.png)

### Annual Change
![Percentage Annual Change By Build Types London 2020 2024](src/ukhpi/images/percentage_annual_change_by_build_types_london_2020_2024.png) ![Percentage Annual Change By Build Types West-Northamptonshire 2020 2024](src/ukhpi/images/percentage_annual_change_by_build_types_west-northamptonshire_2020_2024.png)
![Percentage Annual Change By Occupant Types West-Northamptonshire 2020 2024](src/ukhpi/images/percentage_annual_change_by_occupant_types_west-northamptonshire_2020_2024.png) ![Percentage Annual Change By Payment Types West-Northamptonshire 2020 2024](src/ukhpi/images/percentage_annual_change_by_payment_types_west-northamptonshire_2020_2024.png)
![Percentage Annual Change By Property Types West-Northamptonshire 2020 2024](src/ukhpi/images/percentage_annual_change_by_property_types_west-northamptonshire_2020_2024.png)

### Transaction Volumes
![Sales Volume By Build Types West-Northamptonshire 2020 2024](src/ukhpi/images/sales_volume_by_build_types_west-northamptonshire_2020_2024.png) ![Sales Volume By Payment Types West-Northamptonshire 2020 2024](src/ukhpi/images/sales_volume_by_payment_types_west-northamptonshire_2020_2024.png)

## Notebooks

See `notebooks/try_hpi.ipynb` for a narrated walk-through of the API surface, including data extraction, cleaning, and visualisation examples.

## License

Apache License 2.0. See [`LICENSE`](LICENSE) for full text.

## Author

[Dev Anbarasu](https://github.com/daa2618)
