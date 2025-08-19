from pathlib  import Path
pardir = Path(__file__).parent
import sys
if str(pardir) not in sys.path:
    sys.path.insert(0, str(pardir))

from utils.split_from_camel import make_snake_from_camel
import pandas as pd
import copy
from typing import Union, Optional, List, Dict, Any
from utils.response import Response
from utils.basic_plots import CategoryPlots
from utils.plotly_imports import categorical_color_combinations
from utils.data_loader import Dataset
from utils.data_version import FileVersion

cat_plots = CategoryPlots()



class HousePriceIndex:
    COUNTRIES = ["england", "wales", "scotland", "northern-ireland"]

    def __init__(self):
        self._base_url = "http://landregistry.data.gov.uk/data/ukhpi/region"
        pass
    
    #@staticmethod
    def fetch_hpi(self, 
                  start_year:Union[str,int], 
                  end_year:Optional[Union[str,int]]=None, 
                  region:str="united-kingdom")->Optional[List[Dict[str,Any]]]:

        
        region_key = region.replace(" ", "-").lower()

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
    
    @staticmethod

    def select_values(raw_data_list:List[Dict[str,Any]])->Optional[List[Dict[str,Any]]]:
        
        
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

    def make_df(selected_values:List[Dict[str,Any]])->pd.DataFrame:
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
    def __init__(self, start_year:Union[str, int]=None, end_year:Union[str, int]=None, region:str="united-kingdom"):
        self._start_year = int(start_year) if start_year else 2020
        self._end_year = int(end_year) if end_year else 2024
        self._region = (region.lower().replace(" ", "-"))
        self._hpi = HousePriceIndex()
        self._hpi_df = pd.DataFrame()
        self._file_name = f"hpi_{self._start_year}_{self._end_year}_{self._region}_"
        self._data_path = Path(__file__).resolve().parent/"data"
        if not self.hpi_df.empty and not self.hpi_df is None:
            setattr(self, "PAYMENT_TYPES", ["cash", "mortgage"])
            setattr(self, "OCCUPANT_TYPES", ["first time buyer", "former owner occupier"])
            setattr(self, "BUILD_TYPES", ["existing property", "new build"])
            average_cols = [col for col in self.hpi_df.columns if "average" in col]

            _cols = self.PAYMENT_TYPES.copy()
            _cols.extend(self.OCCUPANT_TYPES)
            _cols.extend(self.BUILD_TYPES)

            property_types = [col.replace("average_price_", "").replace("_", " ")\
                               for col in average_cols if not any(word in \
                                             col.replace("_", " ")\
                                             for word in _cols) and \
                  col != "average_price"]
            
            setattr(self, "PROPERTY_TYPES", property_types)
        
        self._sub_title = f"<br><sup>{self._region.replace("-", " ").upper()} - {self._start_year} to {self._end_year}</sup>"
            
    
    def _fetch_hpi_df(self)->pd.DataFrame:
        #if self._hpi_df.empty:
        data = self._hpi.fetch_hpi(self._start_year, self._end_year, self._region)
        selected = self._hpi.select_values(data)
        df = self._hpi.make_df(selected)
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
        
    
    def plot_sales_volume_new_vs_existing(self):
        if self.sales_volume_new_vs_existing.empty:
            return
        
        sales_volume_new_vs_existing = self.sales_volume_new_vs_existing

        cat_colors = dict(zip(sales_volume_new_vs_existing["new_vs_existing"].unique(), 
                              ['IndianRed', 'LightSalmon']))
        
        cat_plots.df = sales_volume_new_vs_existing

        fig = cat_plots.plot_by_categories(plot_type="Bar", 
                                        x_var = "ref_period_start", 
                                        id_col="new_vs_existing", 
                                        y_var="value", 
                                        colors_dict=cat_colors, 
                                        show_labels=False)
        fig.update_layout(barmode = "stack", 
                    #  barnorm = "percent"
                        )
        
        return cat_plots._update_layout(fig, plot_title=f"Sales Volume New vs. Existing {self._sub_title}")
    

    def _plot_averages(self, avg_category:str):
        cat_upper = avg_category.upper().replace(" ", "_")
        cols = ["average_price"]
        cols.extend([f"average_price_{x.lower().replace(" ", "_")}" for x in getattr(self, cat_upper)])

        df_melt = self.hpi_df.melt(value_vars = cols,
            id_vars = ["ref_period_start"],
            )

        cat_plots.df = df_melt
        fig = cat_plots.plot_by_categories(plot_type="Scatter", 
                                                x_var = "ref_period_start", 
                                                id_col="variable", 
                                                y_var="value", 
                                                colors_dict=None, 
                                                show_labels=False)
        return cat_plots._update_layout(fig, plot_title=f"Average Prices by {avg_category} {self._sub_title}")
    
    def plot_average_price_by_build_types(self):
        return self._plot_averages("BUILD_TYPES")
    
    def plot_average_price_by_occupant_types(self):
        return self._plot_averages("OCCUPANT_TYPES")
    
    def plot_average_price_by_payment_types(self):
        return self._plot_averages("PAYMENT_TYPES")
    
    def plot_average_price_by_property_types(self):
        return self._plot_averages("PROPERTY_TYPES")
    



    

    


        

        
        









    
