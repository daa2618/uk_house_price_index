from __future__ import annotations

import argparse
from pathlib import Path

from ukhpi.postcode_lookups.helper import extract_from_url_and_create_sqlite_db

DEFAULT_URL = "https://www.arcgis.com/sharing/rest/content/items/128bd4b2ad024512beadaf130385d8f8/data"
DEFAULT_DB_DIRECTORY = Path("./data/sqlite_dbs")
DEFAULT_DB_NAME = "postcode_lookups"
DEFAULT_TABLE_NAME = "POSTCODE_LOOKUPS"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download a postcode-lookups ZIP and persist its contents as a SQLite db.",
    )
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help="Source ZIP url.")
    parser.add_argument(
        "--db-directory",
        type=Path,
        default=DEFAULT_DB_DIRECTORY,
        help=f"Directory for the SQLite db (default: {DEFAULT_DB_DIRECTORY}).",
    )
    parser.add_argument(
        "--db-name",
        type=str,
        default=DEFAULT_DB_NAME,
        help=f"SQLite db filename (default: {DEFAULT_DB_NAME}).",
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default=DEFAULT_TABLE_NAME,
        help=f"Table name within the SQLite db (default: {DEFAULT_TABLE_NAME}).",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    db_path = extract_from_url_and_create_sqlite_db(
        url=args.url,
        db_directory=args.db_directory,
        db_name=args.db_name,
        table_name=args.table_name,
    )
    if db_path:
        print(f"SQLite database written to {db_path}")
    else:
        print("Failed to build the SQLite database.")
