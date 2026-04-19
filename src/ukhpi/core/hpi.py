from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

from ukhpi.core.sparql import SparqlQuery
from ukhpi.io.loader import Dataset
from ukhpi.io.versioning import FileVersion

sparqlquery = SparqlQuery()


class HousePriceIndex:
    COUNTRIES = ["england", "wales", "scotland", "northern-ireland"]

    def __init__(self):
        self._base_url = "http://landregistry.data.gov.uk/data/ukhpi/region"
        self._data_path = Path(__file__).resolve().parent.parent / "cache" / "hpi_data"
        self._hpi_regions: Optional[pd.DataFrame] = None

    @property
    def hpi_regions(self) -> pd.DataFrame:
        if self._hpi_regions is None:
            self._hpi_regions = sparqlquery.HPI_REGIONS
        return self._hpi_regions

    @property
    def REGION_TYPES(self) -> List[str]:
        regions = self.hpi_regions
        if regions is None or regions.empty:
            return []
        return list(regions["ref_region_type_keyword"].unique())

    def _fetch_hpi(
        self,
        start_year: Union[str, int],
        end_year: Optional[Union[str, int]] = None,
        region: str = "united-kingdom",
    ) -> pd.DataFrame:
        query = sparqlquery.build_query_for_region(region, start_year, end_year)
        results = sparqlquery.fetch_sparql_query(query)
        return sparqlquery.make_data_from_results(results)

    def fetch_hpi(
        self,
        start_year: Union[str, int],
        end_year: Optional[Union[str, int]] = None,
        region: str = "united-kingdom",
    ) -> pd.DataFrame:
        end_year = end_year if end_year else start_year
        region_key = region.replace(" ", "-").replace("-", "_").lower()
        file = FileVersion(
            base_path=self._data_path,
            file_name=f"{region_key}_{start_year}_{end_year}_hpi",
            extension="csv",
        )

        file_path = file.latest_file_path
        if file_path:
            data = Dataset(file_path=file_path).load_data()
        else:
            data = file.load_latest_file(
                self,
                "_fetch_hpi",
                start_year=start_year,
                end_year=end_year,
                region=region,
                check_version=False,
            )

        return pd.DataFrame(data)
