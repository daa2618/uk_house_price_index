import datetime
import re
from pathlib import Path
from typing import Any

from ukhpi.io.loader import Dataset
from ukhpi.loggers import BasicLogger


class DatesNotFound(Exception):
    pass


class FileVersion:
    """Resolve timestamped cache files like ``{name}_{MMDDYYYY}.{ext}``."""

    def __init__(
        self,
        base_path: Path,
        file_name: str,
        extension: str,
        date_fmt: str = "%m%d%Y",
    ):
        self.base_path = Path(base_path)
        self.file_name = f"{file_name}_" if not file_name.endswith("_") else file_name
        self.extension = f".{extension}" if not extension.startswith(".") else extension
        self.date_fmt = date_fmt
        self._bl = BasicLogger(verbose=False, log_directory=None, logger_name="DATA_VERSION")

    def folder_exists(self) -> bool:
        self.base_path.mkdir(exist_ok=True, parents=True)
        return True

    def get_all_files(self) -> list[Path]:
        self.folder_exists()
        return [fp for fp in self.base_path.iterdir() if fp.is_file() and self.file_name in fp.name]

    def make_file_name(self) -> str:
        stamp = datetime.datetime.now().strftime(self.date_fmt)
        return f"{self.file_name}{stamp}{self.extension}"

    def _fetch_dates_from_file_names(self) -> list[datetime.datetime]:
        if not self.file_name.endswith("_"):
            self.file_name = f"{self.file_name}_"

        name_pat = re.sub(r"\(", r"\\(?", self.file_name)
        name_pat = re.sub(r"\)", r"\\)?", name_pat)
        date_pat = re.sub(r"%m|%Y|%d|%H|%M|%S", "[0-9]+", self.date_fmt)
        date_pat = re.sub(r"%b|%B", "[a-zA-Z]+", date_pat)

        pattern = re.compile(rf"\b{name_pat}{date_pat}{self.extension}")
        matches = [fp for fp in self.base_path.iterdir() if fp.is_file() and pattern.findall(fp.name)]
        if not matches:
            raise DatesNotFound("No dates found for any of the matching file names in the directory")

        dates = [
            datetime.datetime.strptime(re.sub(rf"{name_pat}|\{self.extension}", "", fp.name), self.date_fmt)
            for fp in matches
        ]
        dates.sort()
        return dates

    def check_version(self) -> Any:
        self.folder_exists()
        try:
            dates = self._fetch_dates_from_file_names()
        except DatesNotFound:
            return True

        stale_files = [
            self.base_path / f"{self.file_name}{d.strftime(self.date_fmt)}{self.extension}" for d in dates[:-1]
        ]
        for fp in stale_files:
            try:
                fp.unlink()
            except OSError as e:
                self._bl.debug(f"Failed to remove '{fp}': {e}")

        try:
            latest = dates[-1]
            today = datetime.datetime.now()
            today = datetime.datetime(today.year, today.month, today.day)
            return latest < today
        except (ValueError, IndexError):
            return True

    @property
    def latest_file_path(self) -> Path | None:
        self.folder_exists()
        try:
            dates = self._fetch_dates_from_file_names()
        except DatesNotFound:
            return None

        latest = dates[-1].strftime(self.date_fmt)
        return self.base_path / f"{self.file_name}{latest}{self.extension}"

    def load_latest_file(self, class_name, func, check_version: bool = False, **kwargs):
        from ukhpi.io.writer import WriteFile

        self.folder_exists()

        needs_refresh = True
        try:
            dates = self._fetch_dates_from_file_names()
            today = datetime.datetime.now()
            today = datetime.datetime(today.year, today.month, today.day)
            needs_refresh = dates[-1] < today
        except (DatesNotFound, IndexError, ValueError):
            needs_refresh = True

        if needs_refresh:
            WriteFile(
                data_to_write=getattr(class_name, func)(**kwargs),
                base_path=self.base_path,
                file_name=self.file_name,
                extension=self.extension,
            ).write_file_to_disk(check_version)

        return Dataset(file_path=self.latest_file_path).load_data()
