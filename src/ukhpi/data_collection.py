from __future__ import annotations

from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

import ukhpi
from ukhpi.hpi import HousePriceIndex
from ukhpi.sparql import SparqlQuery

DEFAULT_DATA_PATH = Path(ukhpi.__file__).resolve().parent / "data" / "hpi_data"


class DataCollection:
    def __init__(self, data_path:Path|str, start_year:int=1990, end_year:int=2025):
        self.hpi = HousePriceIndex()
        self.sparql = SparqlQuery()
        self.data_path = Path(data_path)#pardir / "data" / "hpi_data"
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
                    if isinstance(data, pd.DataFrame) and not data.empty:
                        collected_data.append(data)
                except Exception:
                    failed += 1
                    continue
        print(f"Failed to collect data for {failed} regions")
        print(f"Collected data for {n_regions - failed} regions")
        print("#"*100)
        
        if collected_data:
            return pd.concat(collected_data, ignore_index=True)
        return pd.DataFrame()


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ukhpi-collect",
        description="Collect UK House Price Index data for all regions into a local CSV cache.",
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"Directory to write per-region CSVs (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--start-year", type=int, default=1990, help="First year to fetch (default: 1990)."
    )
    parser.add_argument(
        "--end-year", type=int, default=2025, help="Last year to fetch (default: 2025)."
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    DataCollection(
        data_path=args.data_path,
        start_year=args.start_year,
        end_year=args.end_year,
    ).collect_data()


if __name__ == "__main__":
    main()
