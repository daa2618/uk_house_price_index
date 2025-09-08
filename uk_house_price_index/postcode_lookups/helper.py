from helper_tools.zipfile_ops.extract_zipfile import ExtractZipFile #type:ignore
from pathlib import Path
import pandas as pd
from helper_tools.request_soup_data.db_ops.more_sqlite.df2db import Df2Db #type:ignore
from typing import Optional


def extract_from_url_and_create_sqlite_db(url:str, 
                                         db_directory:Path,
                                         db_name:str = None,
                                         verbose:bool=True,
                                         table_name:str = None)->Optional[Path]:
    print(f"Extracting data from {url}")
    try:
        zip_extractor = ExtractZipFile(url = url, 
                                       extract_to_folder=Path("."))
    
        extracted_file_path = zip_extractor.extract_zip_file_to_folder
    except Exception as e:
        print("Extraction failed")
        print(e)
        return 

    if not extracted_file_path:
        print("Extraction failed")
        return
    
        

    print(f"The data was successfully extracted to {extracted_file_path}")

    db_name = db_name if db_name else extracted_file_path.stem.upper().replace(" ", "_")

    db_directory.mkdir(parents=True, exist_ok=True)
    df2db = Df2Db(db_directory=db_directory, 
     db_name=db_name,
     verbose = verbose,
     df_file_path=extracted_file_path)

    table_name = table_name if table_name else db_name.rstrip(".db").upper().replace(" ", "_")

    print(f"Adding the extracted data to the database as table name: '{table_name}'")
    try:
    
        df2db.add_df_to_db_using_sqlalchemy(table_name)
        extracted_file_path.unlink()
        return db_directory/db_name if db_name.endswith(".db") else db_directory/f"{db_name}.db"

    except Exception as e:
        print("Failed to create sqlite database")
        print(e)
        return

    
if __name__ == "__main__":
    postcode_lookups_url = "https://www.arcgis.com/sharing/rest/content/items/128bd4b2ad024512beadaf130385d8f8/data"
    db_path = extract_from_url_and_create_sqlite_db(postcode_lookups_url, 
                                                    db_directory=Path("./data/sqlite_dbs"),
                                                    db_name="postcode_lookups",
                                                    verbose=True,
                                                    table_name="POSTCODE_LOOKUPS")
    if db_path:
        print(f"The sqlite database is available at {db_path}")
    else:
        print("Failed to create the sqlite database")