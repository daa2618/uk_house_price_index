from __future__ import annotations 
from pathlib import Path
import sys
pardir = Path(__file__).parent.parent
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))
from src.hpi import HousePriceIndex
from src.sparql import SparqlQuery
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
class DataCollection:
    def __init__(self, start_year:int=1990, end_year:int=2025):
        self.hpi = HousePriceIndex()
        self.sparql = SparqlQuery()
        self.data_path = pardir / "data" / "hpi_data"
        self.data_path.mkdir(exist_ok=True, parents=True)
        self.start_year = start_year
        self.end_year = end_year
        print("#"*100)
        print(f"Data directory: {self.data_path}")
        print(f"Collecting data for {self.start_year} to {self.end_year}")
        print("#"*100)
        pass
    
    def collect_data(self):
        
        hpi_regions = self.sparql.HPI_REGIONS

        regions = sorted(list(set(hpi_regions["ref_region_keyword"].unique())))
        n_regions = len(regions)
        collected_data = []
        failed = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.hpi.fetch_hpi, self.start_year, self.end_year, region) for region in regions]
            progress= tqdm(as_completed(futures), total=n_regions, desc="Collecting data")
            for future in progress:
                try:
                    data = future.result()
                    if data:
                        collected_data.extend(data)
                except Exception as e:
                    failed += 1
                    continue
        print(f"Failed to collect data for {failed} regions")
        print(f"Collected data for {n_regions - failed} regions")
        print("#"*100)
        return collected_data                        

        

if __name__ == "__main__":
    data_collection = DataCollection()
    data_collection.collect_data()
        
