from ukhpi.io.versioning import FileVersion
from ukhpi.loggers import BasicLogger


class WriteFile(FileVersion):
    """Writes a DataFrame to a timestamped CSV within the cache directory."""

    def __init__(self, data_to_write, **kwargs):
        super().__init__(**kwargs)
        self.data_to_write = data_to_write
        self._bl = BasicLogger(verbose=False, log_directory=None, logger_name="DATA_WRITER")

    def write_file_to_disk(self, check_version: bool = False) -> None:
        self.folder_exists()
        if check_version:
            self.check_version()

        file_path = self.base_path / self.make_file_name()
        if file_path.exists():
            file_path.unlink()

        try:
            self.data_to_write.to_csv(file_path, index=False)
        except Exception as e:
            self._bl.error("Unable to write the content as csv", e)
