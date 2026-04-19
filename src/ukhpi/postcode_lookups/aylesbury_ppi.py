from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from ukhpi.core.ppi import PricePaidData
from ukhpi.loggers import BasicLogger
from ukhpi.postcode_lookups.aylesbury_postcodes import load_aylesbury_postcodes

_log = BasicLogger(verbose=True, log_directory=None, logger_name="AYLESBURY_PPI")


def extract_all_aylesbury_price_paid_data() -> pd.DataFrame | None:
    _log.info("Loading aylesbury postcodes")
    aylesbury_postcodes_df = load_aylesbury_postcodes()

    if aylesbury_postcodes_df is None or aylesbury_postcodes_df.empty:
        _log.debug("Postcodes cannot be loaded")
        return None
    _log.info("Loaded postcodes df")
    all_postcodes = sorted(set(aylesbury_postcodes_df["pcds"].to_list()))

    aylesbury_all_data: list[pd.DataFrame] = []
    n_postcodes = len(all_postcodes)
    _log.info(f"Found {n_postcodes} postcodes in Aylesbury")
    for postcode in tqdm(all_postcodes, desc="Processing postcode", total=n_postcodes):
        postcode_data = PricePaidData(postcode=postcode)
        postcode_df = postcode_data.data_for_postcode
        if postcode_df is None or postcode_df.empty:
            continue
        aylesbury_all_data.append(postcode_df)

    if not aylesbury_all_data:
        return None

    return pd.concat(aylesbury_all_data).reset_index(drop=True)


def make_db_of_results() -> Path | None:
    _log.info("Making db of results")
    aylesbury_all_data_df = extract_all_aylesbury_price_paid_data()

    if aylesbury_all_data_df is None or aylesbury_all_data_df.empty:
        return None

    _log.info(f"Made a dataframe of {len(aylesbury_all_data_df)} rows")

    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True, parents=True)
    csv_fp = data_dir / "aylesbury_ppi.csv"
    aylesbury_all_data_df.to_csv(csv_fp)

    db_directory = Path(__file__).resolve().parent.parent / "cache" / "aylesbury"
    db_directory.mkdir(exist_ok=True, parents=True)
    db_name = "aylesbury_ppi.db"
    table_name = "price_paid_data"
    db_path = db_directory / db_name

    _log.info(f"Adding the extracted data to the database as table name: '{table_name}'")
    try:
        with sqlite3.connect(db_path) as conn:
            aylesbury_all_data_df.to_sql(table_name, conn, if_exists="replace", index=False)
        return db_path
    except Exception as exc:
        _log.debug(f"Failed to create sqlite database: {exc}")
        return None


if __name__ == "__main__":
    make_db_of_results()
