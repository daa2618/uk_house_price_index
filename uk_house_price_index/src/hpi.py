from __future__ import annotations 
from pathlib  import Path
pardir = Path(__file__).parent.parent
import sys
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from helper_utils.split_from_camel import make_snake_from_camel
import pandas as pd
import copy
from typing import Union, Optional, List, Dict, Any
from helper_utils.response import Response
from helper_utils.basic_plots import CategoryPlots, go, px
from helper_utils.plotly_imports import categorical_color_combinations
from helper_utils.data_loader import Dataset
from helper_utils.data_version import FileVersion
from src.sparql import SparqlQuery

cat_plots = CategoryPlots()
sparqlquery = SparqlQuery()


class HousePriceIndex:
    COUNTRIES = ["england", "wales", "scotland", "northern-ireland"]

    def __init__(self):
        self._base_url = "http://landregistry.data.gov.uk/data/ukhpi/region"
        self._hpi_regions = sparqlquery.HPI_REGIONS
        if not self._hpi_regions.empty or not self._hpi_regions is None:
            setattr(self, "REGION_TYPES", list(self._hpi_regions["ref_region_type_keyword"].unique()))
        self._data_path = pardir / "data" / "hpi_data"
        pass
    
    #@staticmethod
    def _fetch_hpi_old(self, 
                  start_year:Union[str,int], 
                  end_year:Optional[Union[str,int]]=None, 
                  region:str="united-kingdom")->Optional[List[Dict[str,Any]]]:

        
        region_key = region.replace(' ', "-").lower()

        data_list = []
        start_year = int(start_year)
        end_year = int(end_year) if end_year else start_year
        
        for year in range(start_year, end_year+1):
            for month in range(1, 13):
                month = str(month) if len(str(month))==2 else f"0{month}"
                url = f"{self._base_url}/{region_key}/month/{year}-{month}.json"
                try:
                    data = Response(url).get_json_from_response()
                except:
                    continue
                if data:
                    #print(url)
                    data_list.append(data)
        if not data_list:
            print(f"Data fetch failed for region: {region}")
            return 

        return data_list
    
    def _fetch_hpi(self, 
                  start_year:Union[str,int], 
                  end_year:Optional[Union[str,int]]=None, 
                  region:str="united-kingdom")->pd.DataFrame:
        
        
        query = sparqlquery.build_query_for_region(region, start_year, end_year)
        results = sparqlquery.fetch_sparql_query(query)
        return sparqlquery.make_data_from_results(results)
    
    def fetch_hpi(self, 
                  start_year:Union[str,int], 
                  end_year:Optional[Union[str,int]]=None, 
                  region:str="united-kingdom"):
        end_year = end_year if end_year else start_year
        region_key = region.replace(' ', "-").replace("-", "_").lower()
        file = FileVersion(
            base_path = self._data_path,
            file_name = f"{region_key}_{start_year}_{end_year}_hpi",
            extension = "csv"
        )

        file_path = file.latest_file_path
        if file_path:
            data = Dataset(file_path = file_path).load_data()
            
        else:
            data = file.load_latest_file(self, 
                    "_fetch_hpi", 
                    start_year=start_year, 
                    end_year=end_year, 
                    region=region,
                    check_version=False)
        
        return pd.DataFrame(data)

    @staticmethod

    def _select_values(raw_data_list:List[Dict[str,Any]])->Optional[List[Dict[str,Any]]]:
        
        
        if not raw_data_list:
            print("Empty data entered")
            return

        
        selected = []
        data_list_copy = copy.deepcopy(raw_data_list)
        for data in data_list_copy:
            data_copy = data.copy()
            primary_topic = data_copy.get("result").get("primaryTopic")
            if not isinstance(primary_topic, dict):
                continue
        
            if "refRegion" in primary_topic:
                reference_region = primary_topic.pop("refRegion")
                #print(reference_region)
                primary_topic["ref_region"] = [label.get("_value") for label in reference_region.get("label")]
        
            if "type" in primary_topic:
                types = primary_topic.pop("type")
                data_type= []
                for type_ in types:
                    if isinstance(type_, dict):
                        label = (type_.get("label"))
                        label_values = [label.get("_value") for label in label]
                        data_type.extend(label_values)
            
                primary_topic["type"] = data_type
            selected.append(primary_topic)

        if not selected:
            print("Value selection failed; Change the region while fetching the data and try again")
            return 

        return selected
    @staticmethod

    def _make_df(selected_values:List[Dict[str,Any]])->pd.DataFrame:
        if not selected_values:
            return pd.DataFrame()
        try:
            df = pd.DataFrame(selected_values)
            df.columns = [make_snake_from_camel(col) for col in df.columns]
            df["ref_period_start"] = pd.to_datetime(df["ref_period_start"])
            return df
        except Exception as e:
            print(e)
            return pd.DataFrame()



class HousePriceIndexPlots:
    def __init__(self, 
                 start_year:Union[str, int]=None, 
                 end_year:Union[str, int]=None, 
                 region:str="united-kingdom"):
        self._start_year = int(start_year) if start_year else 2020
        self._end_year = int(end_year) if end_year else 2024
        self._region = (region.lower().replace(' ', "-")) if region else "all"
        self._hpi = HousePriceIndex()
        self._hpi_df = pd.DataFrame()
        self._file_name = f"hpi_{self._start_year}_{self._end_year}_{self._region}_"
        self._data_path = Path(__file__).resolve().parent/"data"/"region_data"
        if not self.hpi_df.empty and not self.hpi_df is None:
            setattr(self, "PAYMENT_TYPES", ["cash", "mortgage"])
            setattr(self, "OCCUPANT_TYPES", ["first time buyer", "former owner occupier"])
            setattr(self, "BUILD_TYPES", ["existing property", "new build"])
            average_cols = [col for col in self.hpi_df.columns if "average" in col]

            _cols = self.PAYMENT_TYPES.copy()
            _cols.extend(self.OCCUPANT_TYPES)
            _cols.extend(self.BUILD_TYPES)

            property_types = [col.replace("average_price_", "").replace('_', ' ')\
                               for col in average_cols if not any(word in \
                                             col.replace('_', ' ')\
                                             for word in _cols) and \
                  col != "average_price"]
            
            setattr(self, "PROPERTY_TYPES", property_types)
        
        self._sub_title = f"<br><sup>{self._region.replace('-', ' ').upper()} - {self._start_year} to {self._end_year}</sup>"
            
    
    def _fetch_hpi_df(self)->pd.DataFrame:
        #if self._hpi_df.empty:
        df = self._hpi.fetch_hpi(self._start_year, self._end_year, self._region)
        #selected = self._hpi.select_values(data)
        #df = self._hpi.make_df(selected)
        if not df.empty and not df is None:
            return df
         #   self._hpi_df = df

        #return self._hpi_df

    def get_hpi_df(self)->pd.DataFrame:
        file = FileVersion(base_path=self._data_path, file_name=self._file_name, extension="csv")
        file_path = file.latest_file_path
        if file_path:
            data = Dataset(file_path = file_path).load_data()
        else:
            data = file.load_latest_file(self, "_fetch_hpi_df", False)
        if not data:
            return pd.DataFrame()
        
        return pd.DataFrame(data)
    
    @property
    def hpi_df(self)->pd.DataFrame:
        if self._hpi_df.empty:
            df = self.get_hpi_df()
            for col in df.columns:
                try:
                    df[col] = df[col].astype(float)
                except:
                    df[col]= df[col]
            self._hpi_df = df

        return self._hpi_df

    
    @property
    def sales_volume_new_vs_existing(self)->pd.DataFrame:
        
        if not self.hpi_df.empty:
            return self.hpi_df.melt(value_vars=["sales_volume_new_build", "sales_volume_existing_property"],
                               id_vars=["ref_period_start"],
                                      var_name="new_vs_existing",
                                      )
        else:
            return pd.DataFrame
        
    
    #def plot_sales_volume_new_vs_existing(self)->go.Figure:
    #    if self.sales_volume_new_vs_existing.empty:
    #        return
    #
    #    sales_volume_new_vs_existing = self.sales_volume_new_vs_existing
    #
    #    cat_colors = dict(zip(sales_volume_new_vs_existing["new_vs_existing"].unique(),
    #                          ['IndianRed', 'LightSalmon']))
    #
    #    cat_plots.df = sales_volume_new_vs_existing

     #   fig = cat_plots.plot_by_categories(plot_type="Bar", 
     #                                   x_var = "ref_period_start", 
     #                                   id_col="new_vs_existing", 
     #                                   y_var="value", 
     #                                   colors_dict=cat_colors, 
     #                                   show_labels=False)
     #   fig.update_layout(barmode = "stack", 
                    #  barnorm = "percent"
     #                   )
        
     #   return cat_plots._update_layout(fig, plot_title=f"Sales Volume New vs. Existing {self._sub_title}")
    
    def _plot_metric(self, 
                     metric:str, 
                     metric_category:str, 
                     plot_type:str="Scatter")->go.Figure:
        
        cat_upper = metric_category.upper().replace(' ', '_')
        
        metric_lower = metric.lower().replace(' ', '_')

        cols = [metric_lower]
        cols.extend([f"{metric_lower}_{x.lower().replace(' ', '_')}" for x in getattr(self, cat_upper)])

        cols = [col for col in cols if col in self.hpi_df.columns]
        if not cols or self.hpi_df.empty:
            print(f"No data found for {metric} by {metric_category}")
            return go.Figure()
        df_melt = self.hpi_df.melt(value_vars = cols,
            id_vars = ["ref_period_start"],
            )

        
        if plot_type.lower() == "bar":
            df_melt = df_melt.loc[df_melt["variable"]!=metric_lower].reset_index(drop=True)
        
        cat_plots.df = df_melt
        
        colors_dict = dict(
            zip(
                df_melt["variable"].unique(),
                px.colors.sample_colorscale(
                    px.colors.qualitative.Vivid,
                    df_melt["variable"].nunique()
                )
            )
        )

        fig = cat_plots.plot_by_categories(plot_type=plot_type, 
                                                x_var = "ref_period_start", 
                                                id_col="variable", 
                                                y_var="value", 
                                                colors_dict=colors_dict, 
                                                show_labels=True)
        
        metric_title = metric.replace('_', ' ').title()

        fig.update_xaxes(title = "Reference Period Start")
        fig.update_yaxes(title = metric_title)
        return cat_plots._update_layout(fig, plot_title=f"{metric_title} by {cat_upper.replace('_', ' ')} {self._sub_title}")

    def _plot_house_price_index(self, category:str)->go.Figure:
        return self._plot_metric("house_price_index", category)

    def plot_house_price_index_by_build_type(self)->go.Figure:
        return self._plot_house_price_index("BUILD_TYPES")

    def plot_house_price_index_by_property_types(self)->go.Figure:
        return self._plot_house_price_index("PROPERTY_TYPES")

    def plot_house_price_index_by_occupant_types(self)->go.Figure:
        return self._plot_house_price_index("OCCUPANT_TYPES")
    
    def plot_house_price_index_by_payment_types(self)->go.Figure:   
        return self._plot_house_price_index("PAYMENT_TYPES")
    
    def _plot_sales_volume(self, category:str)->go.Figure:
        fig = self._plot_metric("sales_volume", category, "Bar")
        fig.update_layout(barmode = "stack", 
                    #  barnorm = "percent"
                        )
        return fig
    
    def plot_sales_volume_by_build_types(self)->go.Figure:
        return self._plot_sales_volume("BUILD_TYPES")

    def plot_sales_volume_by_payment_types(self)->go.Figure:
        return self._plot_sales_volume("PAYMENT_TYPES")
    def plot_sales_volume_by_property_types(self)->go.Figure:
        return self._plot_sales_volume("PROPERTY_TYPES")
    

    def _plot_averages(self, avg_category:str)->go.Figure:
        return self._plot_metric("average_price", avg_category)

    def plot_average_price_by_build_types(self)->go.Figure:
        return self._plot_averages("BUILD_TYPES")

    def plot_average_price_by_occupant_types(self)->go.Figure:
        return self._plot_averages("OCCUPANT_TYPES")

    def plot_average_price_by_payment_types(self)->go.Figure:
        return self._plot_averages("PAYMENT_TYPES")

    def plot_average_price_by_property_types(self)->go.Figure:
        return self._plot_averages("PROPERTY_TYPES")
    

    def _plot_percentage_annual_change(self, category:str)->go.Figure:
        return self._plot_metric("percentage_annual_change",category)

    def plot_percentage_annual_change_by_build_types(self)->go.Figure:
        return self._plot_percentage_annual_change("BUILD_TYPES")   
    
    def plot_percentage_annual_change_by_occupant_types(self)->go.Figure:
        return self._plot_percentage_annual_change("OCCUPANT_TYPES")

    def plot_percentage_annual_change_by_payment_types(self)->go.Figure:
        return self._plot_percentage_annual_change("PAYMENT_TYPES")

    def plot_percentage_annual_change_by_property_types(self)->go.Figure:
        return self._plot_percentage_annual_change("PROPERTY_TYPES")
    

    


        

        
        









    
