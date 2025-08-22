import pandas as pd
from sparql import SparqlQuery
from hpi import cat_plots, go

sparq = SparqlQuery()

class PricePaidData:
    def __init__(self, postcode:str):
        self._postcode = postcode
        self._postcode_df = pd.DataFrame()
        self._cleaned_df = pd.DataFrame()
        pass

    @property
    def data_for_postcode(self):
        if self._postcode_df.empty:
            self._postcode_df = sparq.get_price_paid_data_for_postcode(self._postcode)
        return self._postcode_df   


    def clean_df(self) -> pd.DataFrame:
        """
        Cleans the postcode data DataFrame by removing rows with NaN values in the 'postcode' column.
        
        Args:
            postcode_data (pd.DataFrame): The DataFrame containing postcode data.
            
        Returns:
            pd.DataFrame: A cleaned DataFrame with rows containing NaN in 'postcode' removed.
        """

        if self.data_for_postcode.empty:
            return self.data_for_postcode
        
        if self._cleaned_df is None or self._cleaned_df.empty:

            results_df = self.data_for_postcode.sort_values("date")
            results_df["paon"] = results_df["paon"].astype(float).astype(int)
            results_df["amount"] = results_df["amount"].astype(float)
            results_df["date"] = pd.to_datetime(results_df["date"])
            results_df = results_df.assign(
                address = [f"{paon}, {street}, {postcode}" for paon, street, postcode in results_df[["paon", "street", "postcode"]].values]
            )
            self._cleaned_df = results_df
        return self._cleaned_df

    def calculate_appreciated_prices(self)-> pd.DataFrame:
        results_df = self.clean_df()
        if results_df.empty:
            return pd.DataFrame()
        out = []
        for address in results_df["address"].unique():
            filtered_for_address =  (
                results_df
                .loc[
                (results_df["address"]==address) & (results_df["category"]=="Standard price paid transaction")
                ]
                .reset_index(drop=True)
            )
            if filtered_for_address.empty:
                continue
            price_change = filtered_for_address["amount"].diff()
            
            n_days = filtered_for_address["date"].diff()
            if price_change.empty or n_days.empty:
                continue
            
            price_change = price_change.sum()
            n_days = n_days.sum().days#.values[-1]
            if not price_change and not n_days:
                continue
            print(f"{address=}; {price_change=}; {n_days=}")
            
            out.append(
                {
                    "address" : address,
                    "price_change" : price_change,
                    "n_days" : n_days,
                    "appreciation_per_day" : price_change / (n_days),
                    "appreciation_per_year" : price_change / (n_days/365)
                }
            )
        if not out:
            return pd.DataFrame()

        return (
        pd.DataFrame(out)
        .sort_values("appreciation_per_year", 
                    ascending=False)
        .reset_index(drop=True)

    )


class PricePaidDataPlots(PricePaidData):
    def __init__(self, postcode):
        super().__init__(postcode)
    


    def plot_property_types(self)->go.Figure:
        cat_plots.df = (
            self.clean_df()
            .drop_duplicates(subset = "address")["property_type"]
            #.groupby("address")["property_type"]
            .value_counts()
            .reset_index()
        )

        fig = cat_plots.group_and_plot(
            plot_type="Pie",
            group_by_var="property_type",
            group_metric="sum",
            y_var="count",
        )

        return cat_plots._update_layout(fig, plot_title="Property Types")

    def plot_price_distribution(self) -> go.Figure:
        cat_plots.df = self.clean_df()
        return
        #return cat_plots._update_layout(fig, plot_title="Price Distribution")
    
    def plot_transaction_distribution(self):
        results_df = self.clean_df()
        cat_plots.df = (
            results_df
            .assign(paon = results_df["paon"].astype(object))
            .groupby("paon", as_index=False)["paon"]
            .value_counts()
        )
        fig = cat_plots.plot_2_dimensional_data("Bar", x_var="paon", y_var="count")
        fig.update_xaxes(type= "category")
        return cat_plots._update_layout(fig, plot_title="Transaction Distribution by Property Number")
    




    
