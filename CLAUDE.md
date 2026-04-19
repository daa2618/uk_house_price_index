# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment & commands

- Dependency management is Poetry (`pyproject.toml`, `poetry.lock`); `requires-python = ">=3.12"`.
- Install: `poetry install`. If the in-project `.venv` is stale (Homebrew Python upgrades leave dead symlinks and Poetry fails with `[Errno 2] No such file or directory: 'python'`), delete both `.venv/` and the cached env under `~/Library/Caches/pypoetry/virtualenvs/uk-house-price-index-*`, then `poetry env use "$(pyenv which python)"` before reinstalling.
- Launch the main dashboard (auto-opens `http://127.0.0.1:8054`): `poetry run python -m ukhpi.dashboard.app_improved`. `app_basic.py` is the minimal variant.
- Regenerate the static plot gallery under `src/ukhpi/images/`: `poetry run python scripts/generate_plots.py` (accepts `--start-year`, `--end-year`, `--region`, `--output-dir`).
- Collect HPI data for every region in bulk: `poetry run python -m ukhpi.core.collection --start-year 1990 --end-year 2025`.
- Run the test suite: `poetry run pytest`. Lint: `poetry run ruff check .` (ruff config lives in `pyproject.toml`: `py312`, line-length 100, rules `E,F,W,I,UP,B`). There is no CI wiring yet.

## External dependency not declared in pyproject.toml

`src/ukhpi/postcode_lookups/*.py` still import from a third-party package called `helper_tools` (`from helper_tools.utils.sys_path_insert import add_to_syspath`, etc.). This package is **not** listed in `pyproject.toml` and must be installed separately for those entry points to run. The core library and dashboard no longer depend on it — the postcode rewrite is scheduled but not yet done.

## Architecture

### Package layout
The package is installed as `ukhpi` from the `src/` layout:

```
src/ukhpi/
├── core/          # SPARQL + HPI fetch/normalise domain (hpi, sparql, ppi, collection)
├── geo/           # ops.py — choropleth + region merging
├── plotting/      # hpi_plots, categories, theme, save
├── io/            # versioning (FileVersion), loader (Dataset), writer (WriteFile), response
├── dashboard/     # app_improved (port 8054), app_basic, assets/
├── postcode_lookups/
├── cache/         # Runtime cache (gitignored): hpi_data/, region_data/, geo_data/
├── images/        # Static plot gallery output
├── loggers.py     # BasicLogger (named loggers.py to avoid shadowing stdlib `logging`)
└── text.py        # String helpers (snake_case, etc.)
```

### Data flow
The core pipeline is SPARQL-first, with a local cache layer in front:

1. `ukhpi.core.sparql :: SparqlQuery` builds SPARQL queries against `http://landregistry.data.gov.uk/landregistry/query` (Land Registry's UK HPI endpoint). Column set is defined by `SparqlQuery._COLUMNS`; the SELECT and OPTIONAL clauses are derived from it. A module-level singleton `sparqlquery = SparqlQuery()` is re-exported for reuse.
2. `ukhpi.core.hpi :: HousePriceIndex.fetch_hpi(start_year, end_year, region)` is the primary entry point. It:
   - Looks for the latest timestamped CSV under `src/ukhpi/cache/hpi_data/` via `FileVersion`.
   - On cache miss, calls `_fetch_hpi` (SPARQL) and persists the result through `FileVersion.load_latest_file`.
   - Returns a tidy `pd.DataFrame`. Region slugs are lowercased with spaces/dashes normalised to underscores for cache filenames but dashes for URLs — see the `region_key` manipulations in `core/hpi.py`.
3. `ukhpi.plotting.hpi_plots :: HousePriceIndexPlots` wraps `HousePriceIndex` and exposes `plot_*` methods producing Plotly figures. `scripts/generate_plots.py` discovers those methods by reflection (`dir(hpi_plots)` filtered by `startswith("plot")`) and saves each via `PlotSaver`.

### Caching & versioning
`ukhpi.io.versioning :: FileVersion` writes files named `{file_name}_{MMDDYYYY}.{ext}` and resolves `latest_file_path` by parsing the date suffix. `load_latest_file(instance, method_name, **kwargs)` re-invokes the given method to refetch data when no cached version exists. Cached datasets live under `src/ukhpi/cache/{hpi_data,region_data,geo_data}/` and are gitignored — regenerate them with the `ukhpi.core.collection` CLI or by triggering a cache-miss fetch.

### Dashboard layer
`ukhpi.dashboard.app_improved` is a single-file Dash app with inline CSS. It imports `HousePriceIndexPlots` and `SparqlQuery` and drives plot selection through dropdowns/sliders. The `assets/` directory is Dash's conventional auto-loaded CSS/JS location.

## Conventions worth preserving

- Region arguments are accepted in any case and with spaces; the code normalises them. Don't tighten this without checking every caller.
- `fetch_hpi` intentionally returns a `DataFrame` (the older `_fetch_hpi_old` that returned a list of raw dicts is kept for reference but unused) — preserve the DataFrame contract.
- New plot methods should begin with `plot_` so `scripts/generate_plots.py` picks them up automatically.
- `HousePriceIndex` and `HousePriceIndexPlots` are lazy — they must not hit SPARQL from `__init__`. Regression tests in `tests/test_hpi.py` pin this behaviour.
- When coercing columns to numeric, avoid `pd.to_numeric(..., errors="ignore")` — it was removed in pandas 2.2+. Use a per-column try/except instead (see `HousePriceIndexPlots.hpi_df`).
- The logger module is `ukhpi.loggers` (not `ukhpi.logging`) to avoid shadowing the stdlib `logging` module.
