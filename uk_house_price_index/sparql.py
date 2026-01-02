from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, List,Any
import pandas as pd
from pathlib  import Path
pardir = Path(__file__).parent
import sys
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from utils.split_from_camel import make_snake_from_camel
from utils.data_loader import Dataset
from utils.data_version import FileVersion
from utils.helper import BasicLogger

class SparqlQuery:
    _PREFIX = """
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            PREFIX sr: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/>
            PREFIX ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
            PREFIX lrppi: <http://landregistry.data.gov.uk/def/ppi/>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX lrcommon: <http://landregistry.data.gov.uk/def/common/>
            """


    _COLUMNS = ['_about', 'averagePrice', 'averagePriceDetached', 'averagePriceExistingProperty', 
            'averagePriceFlatMaisonette', 'averagePriceNewBuild', 'averagePriceSA', 'averagePriceSemiDetached', 
            'averagePriceTerraced', 'dataSet', 'housePriceIndex', 'housePriceIndexDetached', 
            'housePriceIndexExistingProperty', 'housePriceIndexFlatMaisonette', 'housePriceIndexNewBuild', 
            'housePriceIndexSA', 'housePriceIndexSemiDetached', 'housePriceIndexTerraced', 'percentageAnnualChange', 
            'percentageAnnualChangeDetached', 'percentageAnnualChangeExistingProperty', 'percentageAnnualChangeFlatMaisonette', 
            'percentageAnnualChangeNewBuild', 'percentageAnnualChangeSemiDetached', 'percentageAnnualChangeTerraced', 
            'percentageChange', 'percentageChangeDetached', 'percentageChangeExistingProperty', 'percentageChangeFlatMaisonette', 
            'percentageChangeNewBuild', 'percentageChangeSemiDetached', 'percentageChangeTerraced', 'refMonth', 
            'refPeriodDuration', 'refPeriodStart', 'refRegion', 'salesVolume', 'salesVolumeExistingProperty',
            'salesVolumeNewBuild', 'salesVolumeDetached',
            'salesVolumeFlatMaisonette',
            'salesVolumeSemiDetached',
            'salesVolumeTerraced', 'salesVolumeCash', 'salesVolumeMortgage', 'type']

    # SELECT line
    _SELECT_CLAUSE = "SELECT DISTINCT\n  " + "\n  ".join(f"?{col}" for col in _COLUMNS)

    # OPTIONAL lines
    _OPTIONAL_CLAUSE = "\n".join(
        f"  OPTIONAL {{ ?_about ukhpi:{col} ?{col} }}" 
        for col in _COLUMNS if col != "_about"
    )

    def __init__(self, endpoint_url:str = "http://landregistry.data.gov.uk/landregistry/query", verbose:bool = False):
        """
        Initializes the SparqlQuery object.

        """
        self.endpoint_url = endpoint_url
        self.verbose = verbose
        self._hpi_regions = None
        self._logger = BasicLogger(logger_name = "SPARQLQUERY", verbose=False, log_directory=None)


    def build_query_for_region(self, region: str=None, start_year: int = 2020, end_year: int=2024) -> str:
        start_year_str = f"{start_year}-01-01"
        end_year_str = f"{end_year}-12-01"
        
        FILTER_CLAUSE = f"""    
        FILTER ( ?refPeriodStart >= "{start_year_str}"^^xsd:date  &&
                     ?refPeriodStart <= "{end_year_str}"^^xsd:date
                    )
        """
        if region:
            region_lower = region.lower().replace(" ", "-")
            FILTER_CLAUSE = f"""    
        FILTER ( ?refPeriodStart >= "{start_year_str}"^^xsd:date  &&
                     ?refPeriodStart <= "{end_year_str}"^^xsd:date && 
                     ?refRegion IN (<http://landregistry.data.gov.uk/id/region/{region_lower}>)
                    )
        """

        query = f"""
            {self._SELECT_CLAUSE}
            WHERE {{
            ?_about ukhpi:refPeriodStart ?refPeriodStart .

            {self._OPTIONAL_CLAUSE}

            {FILTER_CLAUSE}
            
            }}"""
        return query

    
    def build_query_for_postcode(self, postcode:str)->str:
        postcode = postcode.upper()
        return f"""
                SELECT ?transx ?addr ?paon ?saon ?street ?town ?county ?postcode 
                    ?amount ?date ?category ?recordStatus ?propertyType ?estateType ?transactionId
                WHERE {{
                VALUES ?postcode {{ "{postcode}"^^xsd:string }}

                ?addr lrcommon:postcode ?postcode.

                ?transx lrppi:propertyAddress ?addr ;
                        lrppi:pricePaid ?amount ;
                        lrppi:transactionDate ?date ;
                        lrppi:transactionCategory/skos:prefLabel ?category .

                OPTIONAL {{ ?transx lrppi:transactionId ?transactionId }}
                OPTIONAL {{ ?transx lrppi:recordStatus ?recordStatus }}
                OPTIONAL {{ ?transx lrppi:propertyType/skos:prefLabel ?propertyType }}
                OPTIONAL {{ ?transx lrppi:estateType/skos:prefLabel ?estateType }}

                OPTIONAL {{ ?addr lrcommon:county ?county }}
                OPTIONAL {{ ?addr lrcommon:paon ?paon }}
                OPTIONAL {{ ?addr lrcommon:saon ?saon }}
                OPTIONAL {{ ?addr lrcommon:street ?street }}
                OPTIONAL {{ ?addr lrcommon:town ?town }}
                }}
                ORDER BY ?amount


                """

    def fetch_sparql_query(self, sparql_query:str)->Dict[str,Any]:
        """Fetches data from a SPARQL endpoint using the provided query.

        """
        if not sparql_query.startswith(self._PREFIX):
            sparql_query = self._PREFIX + sparql_query

        # Run the query
        if self.verbose:
            self._logger.info(f"Running SPARQL query: {sparql_query} from {self.endpoint_url}") 

        sparql = SPARQLWrapper(self.endpoint_url)
        sparql.setQuery(sparql_query)
        sparql.setReturnFormat(JSON)
        sparql.setMethod("POST")
        results = sparql.query().convert()
        return results

    @staticmethod
    def make_data_from_results(results: dict) -> pd.DataFrame:
        variables = results.get("head", {}).get("vars", [])
        bindings = results.get("results", {}).get("bindings", [])

        if not bindings:
            return pd.DataFrame(columns=[make_snake_from_camel(v) for v in variables])

        # 1. Create the list of dicts
        data = [{k: v.get("value") for k, v in result.items()} for result in bindings]

        # 2. Initialize DataFrame
        df = pd.DataFrame(data)
        df.columns = [make_snake_from_camel(col) for col in df.columns]

        # 3. Handle Dates using .loc to ensure single-step assignment
        date_cols = ["ref_period_start", "ref_period_end", "date"]
        for col in date_cols:
            if col in df.columns:
                df.loc[:, col] = pd.to_datetime(df[col])

        # 4. Handle Numeric Conversion (Future-proof version)
        for col in df.columns:
            if col not in date_cols:
                try:
                    # Attempt conversion - if it contains non-numeric strings, 
                    # this will raise a ValueError or TypeError
                    converted = pd.to_numeric(df[col], errors='raise')
                    df.loc[:, col] = converted
                except (ValueError, TypeError):
                    # If conversion fails, it's a string column (like a URI or Label)
                    # We just leave it as is.
                    continue

        return df
    

    def _fetch_hpi_regions(self)->pd.DataFrame:
        """Fetches the list of regions from the SPARQL endpoint.

        Returns:
            pd.DataFrame: A DataFrame containing the regions and their URIs.
        """
        query = """

        SELECT DISTINCT ?refRegion ?regionLabel ?regionType
        WHERE {
            ?_about ukhpi:refPeriodStart ?refPeriodStart ;
                    ukhpi:refRegion ?refRegion .

            OPTIONAL { ?refRegion rdfs:label ?regionLabel }
            OPTIONAL { ?refRegion rdf:type ?regionType }

            
        }
        ORDER BY ?refRegion

        """

        results = self.fetch_sparql_query(query)
        df = self.make_data_from_results(results)
        hpi_regions = (
                    df.
                    assign(
                        ref_region_keyword = df["ref_region"].str.split("/").str[-1],
                        ref_region_type_keyword = df["region_type"].str.split("/").str[-1]
                    )
                )
        return hpi_regions
    
    @property
    def HPI_REGIONS(self)->pd.DataFrame:
        if self._hpi_regions is None:

            file = FileVersion(base_path=Path(__file__).resolve().parent/"data"/"region_data", 
                            file_name="hpi_regions_", 
                            extension="csv")
            file_path = file.latest_file_path
            if file_path:
                data = Dataset(file_path = file_path).load_data()
            else:
                data = file.load_latest_file(self, "_fetch_hpi_regions", False)
            if not data:
                return pd.DataFrame()

            self._hpi_regions = pd.DataFrame(data)
        return self._hpi_regions    
    
    def _get_price_paid_data_for_postcode(self, postcode:str)->pd.DataFrame:
        """Fetches price paid data for a given postcode.

        Args:
            postcode (str): The postcode to fetch data for.

        Returns:
            pd.DataFrame: A DataFrame containing the price paid data.
        """
        query = self.build_query_for_postcode(postcode)
        results = self.fetch_sparql_query(query)
        return self.make_data_from_results(results)
    

    def get_price_paid_data_for_postcode(self, postcode:str)->pd.DataFrame:
        file = FileVersion(base_path=Path(__file__).resolve().parent/"data"/"postcode_data", 
                            file_name=f"price_paid_{postcode.upper().replace(' ', '')}_", 
                            extension="csv")
        file_path = file.latest_file_path
        if file_path:
            data = Dataset(file_path = file_path).load_data()
        else:
            data = file.load_latest_file(self, "_get_price_paid_data_for_postcode", False, postcode=postcode)
        if not data:
            return pd.DataFrame()

        return pd.DataFrame(data)
    

    
    


        
        
    



