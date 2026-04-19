from __future__ import annotations

from pathlib import Path
from typing import List, Union

import pandas as pd

from ukhpi.core.hpi import HousePriceIndex
from ukhpi.io.loader import Dataset
from ukhpi.io.versioning import FileVersion
from ukhpi.plotting.categories import cat_plots, go, px


class HousePriceIndexPlots:
    PAYMENT_TYPES = ["cash", "mortgage"]
    OCCUPANT_TYPES = ["first time buyer", "former owner occupier"]
    BUILD_TYPES = ["existing property", "new build"]

    def __init__(
        self,
        start_year: Union[str, int] = None,
        end_year: Union[str, int] = None,
        region: str = "united-kingdom",
    ):
        self._start_year = int(start_year) if start_year else 2020
        self._end_year = int(end_year) if end_year else 2024
        self._region = region.lower().replace(" ", "-") if region else "all"
        self._hpi = HousePriceIndex()
        self._hpi_df = pd.DataFrame()
        self._file_name = f"hpi_{self._start_year}_{self._end_year}_{self._region}_"
        self._data_path = Path(__file__).resolve().parent.parent / "cache" / "region_data"
        self._sub_title = (
            f"<br><sup>{self._region.replace('-', ' ').upper()} - "
            f"{self._start_year} to {self._end_year}</sup>"
        )

    @property
    def PROPERTY_TYPES(self) -> List[str]:
        df = self.hpi_df
        if df.empty:
            return []
        average_cols = [col for col in df.columns if "average" in col]
        excluded = self.PAYMENT_TYPES + self.OCCUPANT_TYPES + self.BUILD_TYPES
        return [
            col.replace("average_price_", "").replace("_", " ")
            for col in average_cols
            if col != "average_price"
            and not any(word in col.replace("_", " ") for word in excluded)
        ]

    def _fetch_hpi_df(self) -> pd.DataFrame:
        return self._hpi.fetch_hpi(self._start_year, self._end_year, self._region)

    def get_hpi_df(self) -> pd.DataFrame:
        file = FileVersion(
            base_path=self._data_path, file_name=self._file_name, extension="csv"
        )
        file_path = file.latest_file_path
        if file_path:
            data = Dataset(file_path=file_path).load_data()
        else:
            data = file.load_latest_file(self, "_fetch_hpi_df", check_version=False)
        if not data:
            return pd.DataFrame()
        return pd.DataFrame(data)

    @property
    def hpi_df(self) -> pd.DataFrame:
        if self._hpi_df.empty:
            df = self.get_hpi_df()
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    continue
            self._hpi_df = df
        return self._hpi_df

    @property
    def sales_volume_new_vs_existing(self) -> pd.DataFrame:
        if self.hpi_df.empty:
            return pd.DataFrame()
        return self.hpi_df.melt(
            value_vars=["sales_volume_new_build", "sales_volume_existing_property"],
            id_vars=["ref_period_start"],
            var_name="new_vs_existing",
        )

    def _plot_metric(
        self, metric: str, metric_category: str, plot_type: str = "Scatter"
    ) -> go.Figure:
        cat_upper = metric_category.upper().replace(" ", "_")
        metric_lower = metric.lower().replace(" ", "_")

        cols = [metric_lower]
        cols.extend(
            [
                f"{metric_lower}_{x.lower().replace(' ', '_')}"
                for x in getattr(self, cat_upper)
            ]
        )
        cols = [col for col in cols if col in self.hpi_df.columns]
        if not cols or self.hpi_df.empty:
            print(f"No data found for {metric} by {metric_category}")
            return go.Figure()

        df_melt = self.hpi_df.melt(value_vars=cols, id_vars=["ref_period_start"])

        if plot_type.lower() == "bar":
            df_melt = df_melt.loc[df_melt["variable"] != metric_lower].reset_index(
                drop=True
            )

        cat_plots.df = df_melt
        colors_dict = dict(
            zip(
                df_melt["variable"].unique(),
                px.colors.sample_colorscale(
                    px.colors.qualitative.Vivid, df_melt["variable"].nunique()
                ),
            )
        )

        fig = cat_plots.plot_by_categories(
            plot_type=plot_type,
            x_var="ref_period_start",
            id_col="variable",
            y_var="value",
            colors_dict=colors_dict,
            show_labels=True,
        )

        metric_title = metric.replace("_", " ").title()
        fig.update_xaxes(title="Reference Period Start")
        fig.update_yaxes(title=metric_title)
        return cat_plots._update_layout(
            fig,
            plot_title=(
                f"{metric_title} by {cat_upper.replace('_', ' ')} {self._sub_title}"
            ),
        )

    def _plot_house_price_index(self, category: str) -> go.Figure:
        return self._plot_metric("house_price_index", category)

    def plot_house_price_index_by_build_type(self) -> go.Figure:
        return self._plot_house_price_index("BUILD_TYPES")

    def plot_house_price_index_by_property_types(self) -> go.Figure:
        return self._plot_house_price_index("PROPERTY_TYPES")

    def plot_house_price_index_by_occupant_types(self) -> go.Figure:
        return self._plot_house_price_index("OCCUPANT_TYPES")

    def plot_house_price_index_by_payment_types(self) -> go.Figure:
        return self._plot_house_price_index("PAYMENT_TYPES")

    def _plot_sales_volume(self, category: str) -> go.Figure:
        fig = self._plot_metric("sales_volume", category, "Bar")
        fig.update_layout(barmode="stack")
        return fig

    def plot_sales_volume_by_build_types(self) -> go.Figure:
        return self._plot_sales_volume("BUILD_TYPES")

    def plot_sales_volume_by_payment_types(self) -> go.Figure:
        return self._plot_sales_volume("PAYMENT_TYPES")

    def plot_sales_volume_by_property_types(self) -> go.Figure:
        return self._plot_sales_volume("PROPERTY_TYPES")

    def _plot_averages(self, avg_category: str) -> go.Figure:
        return self._plot_metric("average_price", avg_category)

    def plot_average_price_by_build_types(self) -> go.Figure:
        return self._plot_averages("BUILD_TYPES")

    def plot_average_price_by_occupant_types(self) -> go.Figure:
        return self._plot_averages("OCCUPANT_TYPES")

    def plot_average_price_by_payment_types(self) -> go.Figure:
        return self._plot_averages("PAYMENT_TYPES")

    def plot_average_price_by_property_types(self) -> go.Figure:
        return self._plot_averages("PROPERTY_TYPES")

    def _plot_percentage_annual_change(self, category: str) -> go.Figure:
        return self._plot_metric("percentage_annual_change", category)

    def plot_percentage_annual_change_by_build_types(self) -> go.Figure:
        return self._plot_percentage_annual_change("BUILD_TYPES")

    def plot_percentage_annual_change_by_occupant_types(self) -> go.Figure:
        return self._plot_percentage_annual_change("OCCUPANT_TYPES")

    def plot_percentage_annual_change_by_payment_types(self) -> go.Figure:
        return self._plot_percentage_annual_change("PAYMENT_TYPES")

    def plot_percentage_annual_change_by_property_types(self) -> go.Figure:
        return self._plot_percentage_annual_change("PROPERTY_TYPES")
