from pathlib import Path
import sys
import pandas as pd

# Add project root to sys.path
pardir = Path(__file__).resolve().parent.parent
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from src.hpi import HousePriceIndex

def verify():
    hpi = HousePriceIndex()
    region = "united-kingdom"
    print(f"Testing fetch_hpi for region: {region}")
    try:
        df = hpi.fetch_hpi(2023, 2024, region)
        print(f"Dataframe type: {type(df)}")
        print(f"Dataframe empty: {df.empty}")
        if not df.empty:
            print(f"Dataframe shape: {df.shape}")
            print("First few rows:")
            print(df.head())
        else:
            print("Dataframe is empty.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    verify()
