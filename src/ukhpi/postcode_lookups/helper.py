from __future__ import annotations

import io
import sqlite3
import zipfile
from pathlib import Path

import pandas as pd
import requests

from ukhpi.loggers import BasicLogger

_log = BasicLogger(verbose=True, log_directory=None, logger_name="POSTCODE_LOOKUPS")


def _download_and_extract_zip(url: str, extract_to: Path) -> Path | None:
    """Download a ZIP file from `url` and extract its first data member into `extract_to`.
    Returns the path of the extracted file, or None on failure.
    """
    extract_to.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        members = [m for m in zf.namelist() if not m.endswith("/")]
        if not members:
            return None
        member = members[0]
        zf.extract(member, path=extract_to)
        return extract_to / member


def _dataframe_to_sqlite(df: pd.DataFrame, db_path: Path, table_name: str) -> None:
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)


def extract_from_url_and_create_sqlite_db(
    url: str,
    db_directory: Path,
    db_name: str | None = None,
    verbose: bool = True,
    table_name: str | None = None,
) -> Path | None:
    _log.info(f"Extracting data from {url}")
    try:
        extracted_file_path = _download_and_extract_zip(url, Path("."))
    except Exception as exc:
        _log.debug(f"Extraction failed: {exc}")
        return None

    if not extracted_file_path:
        _log.debug("Extraction failed: no members in archive")
        return None

    _log.info(f"The data was successfully extracted to {extracted_file_path}")

    stem = extracted_file_path.stem.upper().replace(" ", "_")
    db_name = db_name or stem
    if not db_name.endswith(".db"):
        db_name = f"{db_name}.db"
    db_directory.mkdir(parents=True, exist_ok=True)
    db_path = db_directory / db_name

    table_name = table_name or Path(db_name).stem.upper().replace(" ", "_")

    _log.info(f"Adding the extracted data to the database as table name: '{table_name}'")
    try:
        df = pd.read_csv(extracted_file_path, low_memory=False)
        _dataframe_to_sqlite(df, db_path, table_name)
        extracted_file_path.unlink()
        return db_path
    except Exception as exc:
        _log.debug(f"Failed to create sqlite database: {exc}")
        return None


def query_sqlite(db_path: Path, query: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]
