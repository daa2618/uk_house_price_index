# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment & commands

- Dependency management is Poetry (`pyproject.toml`, `poetry.lock`); `requires-python = ">=3.11"`.
- Install: `poetry install`. If the in-project `.venv` is stale (Homebrew Python upgrades leave dead symlinks and Poetry fails with `[Errno 2] No such file or directory: 'python'`), delete both `.venv/` and the cached env under `~/Library/Caches/pypoetry/virtualenvs/uk-house-price-index-*`, then `poetry env use "$(pyenv which python)"` before reinstalling.
- Launch the main dashboard (auto-opens `http://127.0.0.1:8054`): `python -m uk_house_price_index.dashboard.app_improved`. `app_basic.py` is the minimal variant.
- Regenerate the static plot gallery under `uk_house_price_index/images/`: `python -m uk_house_price_index.hpi_utils.image_generator`.
- There is no test suite, linter config, or CI wiring. Don't invent commands for them.

## External dependency not declared in pyproject.toml

`uk_house_price_index/dashboard/*.py` and `uk_house_price_index/postcode_lookups/*.py` import from a third-party package called `helper_tools` (`from helper_tools.utils.sys_path_insert import add_to_syspath`, etc.). This package is **not** listed in `pyproject.toml` and must be installed separately for those entry points to run. The core library (`src/`, `helper_utils/`, `hpi_utils/image_generator.py`) does not depend on it.

## Architecture

### Data flow
The core pipeline is SPARQL-first, with a local cache layer in front:

1. `src/sparql.py :: SparqlQuery` builds SPARQL queries against `http://landregistry.data.gov.uk/landregistry/query` (Land Registry's UK HPI endpoint). Column set is defined by `SparqlQuery._COLUMNS`; the SELECT and OPTIONAL clauses are derived from it.
2. `src/hpi.py :: HousePriceIndex.fetch_hpi(start_year, end_year, region)` is the primary entry point. It:
   - Looks for the latest timestamped CSV under `uk_house_price_index/data/hpi_data/` via `FileVersion`.
   - On cache miss, calls `_fetch_hpi` (SPARQL) and persists the result through `FileVersion.load_latest_file`.
   - Returns a tidy `pd.DataFrame`. Region slugs are lowercased with spaces/dashes normalised to underscores for cache filenames but dashes for URLs — see the `region_key` manipulations in `hpi.py`.
3. `src/hpi.py :: HousePriceIndexPlots` wraps `HousePriceIndex` and exposes `plot_*` methods producing Plotly figures. `hpi_utils/image_generator.py` discovers those methods by reflection (`dir(hpi_plots)` filtered by `startswith("plot")`) and saves each via `PlotSaver`.

### `helper_utils/` is vendored, not a published package
`helper_utils/` contains local utilities (`FileVersion`, `Dataset`, `Response`, `BasicLogger`, `CategoryPlots`, `PlotSaver`). They are imported two different ways in this repo:

- **From within `helper_utils/` itself**: siblings import each other as top-level modules (`from helper import BasicLogger`), relying on `sys.path.insert(Path(__file__).parent, …)` at the top of each file.
- **From `src/`, `hpi_utils/`, `dashboard/`**: the importer inserts `Path(__file__).parent.parent` (i.e., the package root) into `sys.path`, then imports as `from helper_utils.response import Response`.

When adding new modules, follow whichever convention matches the location — don't "clean up" these `sys.path` manipulations without tracing every importer, because removing them breaks imports in sibling files.

### Caching & versioning
`helper_utils/data_version.py :: FileVersion` writes files named `{file_name}_{MMDDYYYY}.{ext}` and resolves `latest_file_path` by parsing the date suffix. `load_latest_file(instance, method_name, **kwargs)` re-invokes the given method to refetch data when no cached version exists. Cached datasets live under `uk_house_price_index/data/{hpi_data,region_data,geo_data}/`.

### Dashboard layer
`dashboard/app_improved.py` is a single-file Dash app with inline CSS. It imports `HousePriceIndexPlots` and `SparqlQuery` and drives plot selection through dropdowns/sliders. The `assets/` directory is Dash's conventional auto-loaded CSS/JS location.

## Conventions worth preserving

- Region arguments are accepted in any case and with spaces; the code normalises them. Don't tighten this without checking every caller.
- `fetch_hpi` intentionally returns a `DataFrame` (the older `_fetch_hpi_old` that returned a list of raw dicts is kept for reference but unused) — preserve the DataFrame contract.
- New plot methods should begin with `plot_` so `image_generator.py` picks them up automatically.
