import csv
import json
import os
from pathlib import Path


class Dataset:
    """Loads CSV or JSON data from a local file path."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def load_data(self):
        if not self.file_path.exists():
            raise FileNotFoundError(f"File path does not exist: {self.file_path}")

        ext = os.path.splitext(self.file_path)[1].lower().lstrip(".")
        if ext == "csv":
            with self.file_path.open() as f:
                reader = csv.DictReader(f)
                return [{col.replace(" ", "_").lower(): row[col] for col in reader.fieldnames} for row in reader]
        if ext == "json":
            with self.file_path.open() as f:
                return json.load(f)
        raise ValueError(f"Unsupported extension: {ext!r}")
