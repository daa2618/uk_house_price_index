
import os, json
import sys
from pathlib import Path
try:
    parent_dir = Path(__file__).resolve().parent
    parent_dir_str = str(parent_dir)
    if parent_dir_str not in sys.path:
        sys.path.insert(0, parent_dir_str)
    
    from helper import BasicLogger, logging
    from data_version import FileVersion, BasicLogger
    #from utils.verbose_printer import _print
    
except ImportError as e:
    print(f"Failed to import required tools\n{str(e)}")


from datetime import datetime
from json import JSONEncoder



class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class WriteFile(FileVersion):
    """
    Represents a file version that writes data to a file.

    Inherits from FileVersion (assuming a base class managing file versioning).  This class extends
    the functionality to include writing data during initialization.

    Args:
        data_to_write: The data to be written to the file.  The type of this data depends on 
                     the implementation of the underlying file writing mechanism. (e.g., string, bytes, list)
        **kwargs: Keyword arguments passed to the `FileVersion` constructor.  This allows for 
                  reusing existing file versioning logic.  Example kwargs might include file path, 
                  version number, etc.
    """
    def __init__(self, data_to_write, debug:bool=False, **kwargs):
        super().__init__(debug=debug, **kwargs)
        self.data_to_write = data_to_write
        self.debug = debug
        self._bl = BasicLogger(verbose = False, 
        log_level = logging.DEBUG if debug else logging.INFO,
        log_directory=None, logger_name="DATA WRITER")
        
    def _write_file_to_disk(self, check_version:bool)->None:
        """
        Writes data to a file on disk.

        This method checks if the designated folder exists, optionally checks a version, 
        creates a filename, and writes the data to a file with the appropriate extension (.json or .csv).
        It handles potential errors like file already existing and data type mismatches.

        Args:
            check_version (bool): If True, performs a version check before writing the file.

        Raises:
            TypeError: If the data to be written is not compatible with the specified file extension (json or csv).  Provides a descriptive error message indicating the data type and the expected type.
            
        Returns:
            None. Prints a confirmation message upon successful file writing.

        Check version should be a bool\nSet check_version=True to remove older files\nSetting check_version=False will keep the files that are at least a day old"""
        if self.folder_exists():
            if check_version:
                self.check_version()
            #else:
            #if self.check_version():
            if not "." in self.extension:
                extension = f".{self.extension}"
            file_path = os.path.join(self.base_path, self.make_file_name())

            self._bl.debug(f"Writing the file at {(os.path.abspath(file_path))}....")
            for file in os.listdir(self.base_path):
                if file == self.make_file_name():
                    os.remove(file_path)

            if "json" in self.extension:
                try:

                    with open(file_path, "x") as f:
                        f.write(json.dumps(self.data_to_write,indent=4,cls=DateTimeEncoder))

                except Exception as e:
                    self._bl.error(f"Unable to write the content as json", e)
                    #raise TypeError(f"The file to write is of type {type(self.data_to_write)}.\nTherefore, cannot be saved as a json file")

            elif "csv" in self.extension:
                try:
                    self.data_to_write.to_csv(file_path, index=False)
                except Exception as e:
                    self._bl.error(f"Unable to write the content as csv", e)
                    #raise TypeError(f"The file to write is of type {type(self.data_to_write)}.\nTherefore, cannot be saved as a csv file")

            elif "pdf" in self.extension:
                try:
                    with open(file_path, "wb") as f:
                        f.write(self.data_to_write)
                except Exception as e:
                    self._bl.error(f"Unable to write the content as pdf", e)

            elif "txt" in self.extension:
                try:
                    with open(file_path, mode = "w", encoding="utf-8") as f:
                        f.write(self.data_to_write)
                except Exception as e:
                    self._bl.error(f"Unable to write the content as txt", e)
            
            elif "xls" in self.extension:
                df = self.data_to_write
                try:
                    df.to_excel(file_path, index=False)
                except Exception as e:
                    self._bl.error("Unable to write the content as an excel file", e)


            return None
    
    def write_file_to_disk(self, check_version:bool)->None:
        try:
            self._write_file_to_disk(check_version=check_version)
            self._bl.debug(f"The file has been written")
        except Exception as e:
            self._bl.error("Data Writer failed", e)
        
    

        