from pathlib import Path
from helper_tools.utils.sys_path_insert import add_to_syspath #type:ignore
add_to_syspath(Path(__file__).parent.parent)
print("Importing PricePaidData from ppi")
from ppi import PricePaidData
print("Importing load_aylesbury_postcodes")
from postcode_lookups.aylesbury_postcodes import load_aylesbury_postcodes
from tqdm import tqdm
import pandas as pd
from typing import Optional
print("Importing Df2Db")
from helper_tools.request_soup_data.db_ops.more_sqlite.df2db import Df2Db #type:ignore
print("All imports complete")
def extract_all_aylesbury_price_paid_data()->Optional[pd.DataFrame]:
    print("Loading aylesbury postcodes")
    aylesbury_postcodes_df = load_aylesbury_postcodes()
    
    if aylesbury_postcodes_df is None or aylesbury_postcodes_df.empty:
        print("Postcodes cannot be loaded")
        return
    print("Loaded postcodes df")
    all_postcodes = sorted(list(set(aylesbury_postcodes_df["pcds"].to_list())))

    
    aylesbury_all_data = []
    n_postcodes = len(all_postcodes)
    print(f"Found {n_postcodes} postcodes in Aylesbury")
    for postcode in tqdm(all_postcodes, desc="Processing postcode", total=n_postcodes):
        postcode_data = PricePaidData(postcode = postcode)
        postcode_df = postcode_data.data_for_postcode
        if postcode_df is None or postcode_df.empty:
            continue
        aylesbury_all_data.append(postcode_df)
    
    if not aylesbury_all_data:
        return
    
    aylesbury_all_data_df = (
        pd.concat(
            aylesbury_all_data
        )
        .reset_index(drop=True)
    )

    return aylesbury_all_data_df


def make_db_of_results()->Optional[Path]:
    print("Making db of results")
    aylesbury_all_data_df = extract_all_aylesbury_price_paid_data()

    if aylesbury_all_data_df is None or aylesbury_all_data_df.empty:
        return
    
    print(f"Made a dataframe of {len(aylesbury_all_data_df)} rows")
    print(f"Top 5 rows: {aylesbury_all_data_df.head()}")
    print("="*127)
    print(f"Bottom 5 rows: {aylesbury_all_data_df.tail()}")

    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True, parents=True)
    csv_fp = data_dir/"aylesbury_ppi.csv"

    aylesbury_all_data_df.to_csv(csv_fp)
    
    db_directory = Path(r"D:\dev\uk_hpi\aylesbury")
    db_name = "aylesbury_ppi.db"
    table_name = "price_paid_data"

    df2db = Df2Db(db_directory=db_directory, 
     db_name=db_name,
     verbose = True,
     df_file_path=csv_fp)
    
    print(f"Adding the extracted data to the database as table name: '{table_name}'")
    try:
    
        df2db.add_df_to_db_using_sqlalchemy(table_name)
        #csv_fp.unlink()
        return db_directory/db_name if db_name.endswith(".db") else db_directory/f"{db_name}.db"

    except Exception as e:
        print("Failed to create sqlite database")
        print(e)
        return
    
    
if __name__ == "__main__":
    make_db_of_results()






    








