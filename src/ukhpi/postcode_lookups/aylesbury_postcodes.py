from __future__ import annotations

from pathlib import Path

import pandas as pd

from ukhpi.loggers import BasicLogger
from ukhpi.postcode_lookups import helper

_log = BasicLogger(verbose=True, log_directory=None, logger_name="AYLESBURY_POSTCODES")


def make_aylesbury_postcodes() -> pd.DataFrame | None:
    """Create a DataFrame of postcodes for the Aylesbury area.

    ### Get Output Area (2021) to Ward (2025) to LAD (May 2025) Best Fit Lookup in EW (V2)
    - Download as a csv file from https://geoportal.statistics.gov.uk/datasets/ons::output-area-2021-to-ward-2025-to-lad-may-2025-best-fit-lookup-in-ew-v2/about

    ### Get Postcode to Postcode Sector to Postcode District to Postcode Area (August 2022) to Output Area (2021) Lookup in EW
    - Download as a zip file from https://www.arcgis.com/sharing/rest/content/items/3b911871ef6044f4ad6c838a56c04475/data
    """
    data_dir = Path(__file__).parent / "data"
    oa_ward_lookup_file = data_dir / "oa21_to_ward25_to_lad25_lookup.csv"
    if not oa_ward_lookup_file.exists():
        return pd.DataFrame()

    oa_ward_lookup_df = pd.read_csv(oa_ward_lookup_file, low_memory=False)
    oa_ward_lookup_df.columns = [x.lower() for x in oa_ward_lookup_df.columns]

    db_directory = data_dir / "sqlite_dbs"
    db_name = "postcode_postcode_sector_postcode_district_lookup.db"
    table_name = "postcode_lookup"
    db_path = db_directory / db_name
    if not db_path.exists():
        db_path = helper.extract_from_url_and_create_sqlite_db(
            url="https://www.arcgis.com/sharing/rest/content/items/3b911871ef6044f4ad6c838a56c04475/data",
            db_directory=db_directory,
            db_name=db_name,
            table_name=table_name,
        )

    oa21cd_aylesbury = oa_ward_lookup_df.loc[
        oa_ward_lookup_df["wd25nm"].str.lower().str.contains("aylesbury"), "oa21cd"
    ].to_list()

    placeholders = ",".join([f"'{x}'" for x in oa21cd_aylesbury])
    query = f"""
    SELECT *
    FROM {table_name}
    WHERE oa21 IN ({placeholders})
    """
    results = helper.query_sqlite(db_path, query)

    aylesbury_postcodes_df = pd.merge(
        pd.DataFrame(results),
        oa_ward_lookup_df,
        left_on="oa21",
        right_on="oa21cd",
        how="left",
    )

    aylesbury_postcodes_df.to_csv(data_dir / "aylesbury_postcodes.csv", index=False)
    return aylesbury_postcodes_df


def load_aylesbury_postcodes() -> pd.DataFrame | None:
    data_dir = Path(__file__).parent / "data"
    aylesbury_postcodes_file = data_dir / "aylesbury_postcodes.csv"
    if not aylesbury_postcodes_file.exists():
        _log.info("CSV file not found — regenerating from source lookups")
        return make_aylesbury_postcodes()

    return pd.read_csv(aylesbury_postcodes_file, low_memory=False)
