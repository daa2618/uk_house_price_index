from __future__ import annotations
from pathlib import Path
import geopandas as gpd
import pandas as pd
pardir = Path(__file__).parent
import sys
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from utils.data_version import FileVersion
from hpi import HousePriceIndex
import plotly.express as px
from typing import Dict, List

class GeoOps:
    
    def __init__(self, map_style:str="open-street-map"):
        self._ref_geo_df = pd.DataFrame()
        self.file_path = Path(__file__).parent / "data" / "geo_data" / "georef_united_kingdom_county_unitary_authority.geojson"
        self.file_path.parent.mkdir(exist_ok=True, parents=True)
        self.hpi_by_geo_dict = {}
        self.supported_geo_types = ["ctry_name", "rgn_name", "ctyua_name"]
        self.numeric_cols:List[str] = [
            'average_price',
            'average_price_detached',
            'average_price_existing_property',
            'average_price_flat_maisonette',
            'average_price_new_build',
            'average_price_sa',
            'average_price_semi_detached',
            'average_price_terraced',
            'house_price_index',
            'house_price_index_detached',
            'house_price_index_existing_property',
            'house_price_index_flat_maisonette',
            'house_price_index_new_build',
            'house_price_index_sa',
            'house_price_index_semi_detached',
            'house_price_index_terraced',
            'percentage_annual_change',
            'percentage_annual_change_detached',
            'percentage_annual_change_existing_property',
            'percentage_annual_change_flat_maisonette',
            'percentage_annual_change_new_build',
            'percentage_annual_change_semi_detached',
            'percentage_annual_change_terraced',
            'percentage_change',
            'percentage_change_detached',
            'percentage_change_existing_property',
            'percentage_change_flat_maisonette',
            'percentage_change_new_build',
            'percentage_change_semi_detached',
            'percentage_change_terraced',
            'sales_volume',
            'sales_volume_existing_property',
            'sales_volume_new_build',
            'sales_volume_cash',
            'sales_volume_mortgage']
        
        self.map_style=map_style
        
        pass

    @property
    def REF_GEO_DF(self) -> gpd.GeoDataFrame:
        if not self._ref_geo_df.empty:
            return self._ref_geo_df

        if self.file_path.exists():
            self._ref_geo_df = gpd.read_file(self.file_path)
            return self._ref_geo_df
        
        url = "https://data.opendatasoft.com/api/explore/v2.1/catalog/datasets/georef-united-kingdom-county-unitary-authority@public/exports/geojson?lang=en&timezone=Europe%2FLondon"
    
        # 1. Use .copy() to break the chain from the internal reader
        gdf = gpd.read_file(url).copy()
        
        # 2. Re-assign instead of inplace=True
        gdf = gdf.set_crs(epsg=4326, allow_override=True)

        # 3. Efficient column cleaning
        for col in gdf.columns:
            # Check if the column actually contains lists before trying to join
            # This is safer than a try/except block
            mask = gdf[col].apply(lambda x: isinstance(x, list))
            if mask.any():
                gdf.loc[mask, col] = gdf.loc[mask, col].apply(lambda x: ",".join(map(str, x)))

        # Path logic
        
        gdf.to_file(self.file_path, driver="GeoJSON")

        self._ref_geo_df = gdf
            
        return self._ref_geo_df
    
    def get_data_for_geo(self, 
                         start_year:int, 
                         end_year:int, 
                         geo_type_id:str, 
                         ref_month:str):
        
        
        if geo_type_id not in self.supported_geo_types:
            raise ValueError(f"Geo type {geo_type_id} not found in supported geo types. Supported geo types are {self.supported_geo_types}")

        hpi_by_geo = self.hpi_by_geo_dict.get(geo_type_id)

        if  hpi_by_geo is None or hpi_by_geo.empty:
            
            hpi = HousePriceIndex()
            
            
            dfs = []

            for geo_name in self.REF_GEO_DF[geo_type_id].unique():
                result = None
                try:
                    result = hpi.fetch_hpi(start_year=start_year, 
                                        end_year=end_year, 
                                        region=geo_name)
                except Exception as e:
                    print(e)
                    continue
                if result is None or result.empty:
                    continue
                dfs.append(result)
                

            hpi_by_geo = pd.concat(dfs, ignore_index=True)
            if hpi_by_geo.empty or hpi_by_geo is None:
                print("Empty data entered")
                return pd.DataFrame()
            
            if ref_month not in hpi_by_geo["ref_month"].unique():
                print(f"Ref month {ref_month} not found in the data")
                return pd.DataFrame()
            
            if "ref_region" not in hpi_by_geo.columns:
                print("Ref region not found in the data")
                return pd.DataFrame()
            
            if "ref_month" not in hpi_by_geo.columns:
                print("Ref month not found in the data")
                return pd.DataFrame()
            hpi_by_geo.index = hpi_by_geo["ref_region"].apply(
                lambda x: x.split("/")[-1].replace("-", " ").title()
            )
            hpi_by_geo.index.name = geo_type_id

            


            numeric_cols = [col for col in hpi_by_geo.columns \
            if any(word in col for word in \
                ["price", "percent", "volume"])]
            
            self.numeric_cols = numeric_cols

            # Create a dictionary of the converted columns
            updates = {}
            for col in numeric_cols:
                updates[col] = pd.to_numeric(hpi_by_geo[col], errors='coerce')

            # Assign them all at once to a fresh copy
            hpi_by_geo = hpi_by_geo.assign(**updates)
            self.hpi_by_geo_dict[geo_type_id] = hpi_by_geo  


        
        geo_polygons_dissolved = self.REF_GEO_DF.dissolve(by=geo_type_id)

        hpi_for_month = hpi_by_geo.loc[hpi_by_geo["ref_month"]==ref_month]

        merged_df = pd.merge(
            geo_polygons_dissolved.reset_index()[[geo_type_id, "geometry"]],
            hpi_for_month.reset_index(),
            left_on=geo_type_id,
            right_on=geo_type_id,
            how="left"
        ).set_index(geo_type_id)

        return merged_df

    
    def _plot_hpi_by_geo(self,
                         merged_df:gpd.GeoDataFrame, 
                         metric:str, 
                         geo_type:str, 
                         ref_month:str)->px.Figure:
        metric_title = metric.replace("_", " ").title()
        geo_type_name = geo_type.title()


        fig = px.choropleth_map(
            data_frame=merged_df,
            locations=merged_df.index,
            geojson=merged_df.geometry,
            color=metric,
            
            color_continuous_scale="Viridis",
            #scope="europe",
            opacity=0.5,
            center = {"lat": 54.0022,  "lon": -2.5420},
            zoom = 4,
            map_style=self.map_style,
            
        )



        fig.update_geos(
            fitbounds="locations", 
            visible=False
        )
        fig.update_layout(
            title={
                "text" : f'{metric_title} by {geo_type_name} for period {ref_month}<br>(Hover for breakdown)',
                "x" : 0,
                "y" : 0.9,
                "font" : {"color" : "black"}
            },            
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        return fig
    
    def plot_hpi_by_geo(self, 
                        start_year:int, 
                        end_year:int, 
                        geo_type_id:str, 
                        ref_month:str,
                        metric:str):
        """
        Plot the HPI by geo type

        Args:
            start_year (int): Start year
            end_year (int): End year
            geo_type_id (str): Geo type id, must be one of "ctry_name", "rgn_name", "ctyua_name"
            ref_month (str): Reference month, format YYYY-MM
            metric (str): Metric to plot

        Returns:
            px.Figure: Plot of HPI by geo type
        """

        if self.numeric_cols and metric not in self.numeric_cols:
            raise ValueError(f"Metric {metric} not found in the data. Supported metrics are {self.numeric_cols}")
        
        merged_df = self.get_data_for_geo(start_year, end_year, geo_type_id, ref_month)
        return self._plot_hpi_by_geo(merged_df, metric, geo_type_id, ref_month)
        
    

    
