import logging
import os


class BasicLogger:
    """Thin wrapper around ``logging.Logger`` with optional file output."""

    def __init__(
        self,
        logger_name: str = "basic_app",
        log_level: int = logging.INFO,
        log_directory: str | None = "logs",
        log_file_name: str | None = None,
        log_file_extension: str = ".log",
        log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        date_format: str = "%Y-%m-%d %H:%M:%S",
        log_to_console: bool = True,
        verbose: bool = True,
    ):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False

        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()

        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

        if log_directory and (log_file_name or logger_name):
            log_dir = log_directory if os.path.isabs(log_directory) else os.path.join(os.getcwd(), log_directory)
            os.makedirs(log_dir, exist_ok=True)
            file_name = log_file_name or logger_name
            if not log_file_extension.startswith("."):
                log_file_extension = f".{log_file_extension}"
            file_handler = logging.FileHandler(os.path.join(log_dir, f"{file_name}{log_file_extension}"))
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        if log_to_console and verbose:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def debug(self, message: str, *args, **kwargs):
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, exc_info=None, **kwargs):
        self.logger.error(message, *args, exc_info=exc_info, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        self.logger.exception(message, *args, **kwargs)
