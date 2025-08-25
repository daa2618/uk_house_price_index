from pathlib import Path
import geopandas as gpd
pardir = Path(__file__).parent
import sys
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from utils.data_version import FileVersion

class GeoOps:
    
    def __init__(self):
        self._ref_geo_df = gpd.GeoDataFrame()
        pass

    @property
    def REF_GEO_DF(self)->gpd.GeoDataFrame:
    
        if self._ref_geo_df.empty:

            unitary_authority_geo = gpd.read_file("https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-united-kingdom-county-unitary-authority@public/exports/geojson?lang=en&timezone=Europe%2FLondon")
            
            georef_united_kingdom_county_unitary_authority = gpd.GeoDataFrame(unitary_authority_geo)
            
            georef_united_kingdom_county_unitary_authority.set_crs(4326, inplace=True)

            for col in georef_united_kingdom_county_unitary_authority.columns:
                try:
                    georef_united_kingdom_county_unitary_authority[col] = georef_united_kingdom_county_unitary_authority[col].apply(lambda x: ",".join(x) if isinstance(x, list) else x)
                except:
                    georef_united_kingdom_county_unitary_authority[col] = georef_united_kingdom_county_unitary_authority[col]


            
            file_path:Path = Path(__file__).parent/"data"/"geo_data"
            file_path = file_path if file_path.name == "georef_united_kingdom_county_unitary_authority.geojson" else file_path/"georef_united_kingdom_county_unitary_authority.geojson"
            data_path = file_path.resolve().parent

            data_path.mkdir(exist_ok=True, parents = True)
            
            georef_united_kingdom_county_unitary_authority.to_file(file_path, driver = "GeoJSON")

            self._ref_geo_df = georef_united_kingdom_county_unitary_authority
        return self._ref_geo_df
    
