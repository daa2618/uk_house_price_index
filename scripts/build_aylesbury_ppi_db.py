from __future__ import annotations

import argparse
from pathlib import Path

from ukhpi.postcode_lookups.aylesbury_ppi import (
    DEFAULT_CSV_PATH,
    DEFAULT_DB_DIRECTORY,
    DEFAULT_DB_NAME,
    DEFAULT_TABLE_NAME,
    make_db_of_results,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch Aylesbury price-paid data and persist it as CSV + SQLite.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=DEFAULT_CSV_PATH,
        help=f"Output CSV path (default: {DEFAULT_CSV_PATH}).",
    )
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
    db_path = make_db_of_results(
        csv_path=args.csv_path,
        db_directory=args.db_directory,
        db_name=args.db_name,
        table_name=args.table_name,
    )
    if db_path:
        print(f"SQLite database written to {db_path}")
    else:
        print("Failed to build the SQLite database.")
