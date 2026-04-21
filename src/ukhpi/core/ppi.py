from __future__ import annotations

import numpy as np
import pandas as pd

from ukhpi.core.sparql import SparqlQuery
from ukhpi.plotting.categories import cat_plots, go
from ukhpi.plotting.theme import make_subplots, px

sparq = SparqlQuery()


class PricePaidData:
    def __init__(self, postcode: str):
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

            if "record_status" in results_df.columns:
                status = results_df["record_status"].astype(str).str.strip().str.lower()
                # Status may be a bare label ("Add") or a full URI (".../def/ppi/add").
                suffix = status.str.rsplit("/", n=1).str[-1]
                keep = suffix.isin({"add", ""}) | suffix.isna()
                results_df = results_df.loc[keep]

            if "transaction_id" in results_df.columns:
                results_df = results_df.drop_duplicates(subset="transaction_id", keep="last")

            try:
                results_df["paon"] = results_df["paon"].astype(float).astype(int)
            except (ValueError, TypeError):
                results_df["paon"] = results_df["paon"].astype(str)

            results_df["amount"] = results_df["amount"].astype(float)
            results_df["date"] = pd.to_datetime(results_df["date"])

            saon_series = (
                results_df["saon"].fillna("").astype(str).str.strip()
                if "saon" in results_df.columns
                else pd.Series([""] * len(results_df), index=results_df.index)
            )
            results_df = results_df.assign(
                address=[
                    f"{paon}{' ' + saon if saon else ''}, {street}, {postcode}"
                    for paon, saon, street, postcode in zip(
                        results_df["paon"],
                        saon_series,
                        results_df["street"],
                        results_df["postcode"],
                        strict=False,
                    )
                ]
            )
            self._cleaned_df = results_df
        return self._cleaned_df

    def calculate_appreciated_prices(self) -> pd.DataFrame:
        results_df = self.clean_df()
        if results_df.empty:
            return pd.DataFrame()
        out = []
        for address in results_df["address"].unique():
            filtered = (
                results_df.loc[
                    (results_df["address"] == address) & (results_df["category"] == "Standard price paid transaction")
                ]
                .sort_values("date")
                .reset_index(drop=True)
            )
            if len(filtered) < 2:
                continue

            p_start = float(filtered["amount"].iloc[0])
            p_end = float(filtered["amount"].iloc[-1])
            hold_days = (filtered["date"].iloc[-1] - filtered["date"].iloc[0]).days
            if hold_days <= 0 or p_start <= 0:
                continue

            price_change = p_end - p_start
            hold_years = hold_days / 365.0
            cagr_pct = ((p_end / p_start) ** (1.0 / hold_years) - 1.0) * 100.0

            out.append(
                {
                    "address": address,
                    "first_date": filtered["date"].iloc[0],
                    "last_date": filtered["date"].iloc[-1],
                    "p_start": p_start,
                    "p_end": p_end,
                    "hold_years": hold_years,
                    "price_change": price_change,
                    "cagr_pct": cagr_pct,
                }
            )
        if not out:
            return pd.DataFrame()

        return pd.DataFrame(out).sort_values("cagr_pct", ascending=False).reset_index(drop=True)


class PricePaidDataPlots(PricePaidData):
    def __init__(self, postcode):
        super().__init__(postcode)

    def plot_property_types(self) -> go.Figure:
        cat_plots.df = (
            self.clean_df()
            .drop_duplicates(subset="address")["property_type"]
            # .groupby("address")["property_type"]
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
        df = self.clean_df()
        fig = go.Figure()
        if df.empty:
            return fig.update_layout(title=dict(text="<b>PRICE DISTRIBUTION</b>", x=0.5))

        amounts = df["amount"].dropna()
        fig.add_trace(go.Histogram(x=amounts, nbinsx=30, name="Transactions"))
        if not amounts.empty:
            median = float(amounts.median())
            fig.add_vline(
                x=median,
                line_dash="dash",
                line_color="#2ecc71",
                annotation_text=f"Median £{median:,.0f}",
                annotation_position="top right",
            )
        fig.update_layout(
            title=dict(text="<b>PRICE DISTRIBUTION</b>", x=0.5),
            xaxis_title="Sale price (£)",
            yaxis_title="Transactions",
            bargap=0.05,
        )
        return fig

    def plot_price_timeline(self) -> go.Figure:
        df = self.clean_df()
        fig = go.Figure()
        if df.empty:
            return fig.update_layout(title=dict(text="<b>PRICE OVER TIME</b>", x=0.5))

        data = df.dropna(subset=["amount", "date"]).sort_values("date")
        color_col = "property_type" if "property_type" in data.columns else None
        fig = px.scatter(
            data,
            x="date",
            y="amount",
            color=color_col,
            hover_data=["address"] if "address" in data.columns else None,
        )
        fig.update_traces(marker=dict(size=9, opacity=0.8))

        if len(data) >= 2:
            x_ord = data["date"].map(pd.Timestamp.toordinal).to_numpy(dtype=float)
            y = data["amount"].to_numpy(dtype=float)
            slope, intercept = np.polyfit(x_ord, y, 1)
            xs = np.array([x_ord.min(), x_ord.max()])
            ys = slope * xs + intercept
            trend_x = [pd.Timestamp.fromordinal(int(v)) for v in xs]
            fig.add_trace(
                go.Scatter(
                    x=trend_x,
                    y=ys,
                    mode="lines",
                    line=dict(color="#e67e22", dash="dash", width=2),
                    name="Trend (OLS)",
                )
            )

        fig.update_layout(
            title=dict(text="<b>PRICE OVER TIME</b>", x=0.5),
            xaxis_title="Sale date",
            yaxis_title="Sale price (£)",
        )
        return fig

    def plot_property_type_medians(self) -> go.Figure:
        df = self.clean_df()
        fig = go.Figure()
        if df.empty or "property_type" not in df.columns:
            return fig.update_layout(title=dict(text="<b>MEDIAN PRICE BY PROPERTY TYPE</b>", x=0.5))

        grouped = (
            df.dropna(subset=["amount", "property_type"])
            .groupby("property_type")["amount"]
            .agg(median="median", count="count")
            .reset_index()
            .sort_values("median", ascending=False)
        )
        fig.add_trace(
            go.Bar(
                x=grouped["property_type"],
                y=grouped["median"],
                text=[f"n={n}" for n in grouped["count"]],
                textposition="outside",
                marker_color="#3498db",
                name="Median price",
            )
        )
        fig.update_layout(
            title=dict(text="<b>MEDIAN PRICE BY PROPERTY TYPE</b>", x=0.5),
            xaxis_title="Property type",
            yaxis_title="Median sale price (£)",
            showlegend=False,
        )
        return fig

    def plot_tenure_mix(self) -> go.Figure:
        df = self.clean_df()
        if df.empty or "estate_type" not in df.columns:
            fig = go.Figure()
            return fig.update_layout(title=dict(text="<b>TENURE MIX</b>", x=0.5))

        tenure = df.dropna(subset=["estate_type"])
        grouped = tenure.groupby("estate_type")["amount"].agg(count="count", median="median").reset_index()
        fig = make_subplots(
            rows=1,
            cols=2,
            specs=[[{"type": "domain"}, {"type": "xy"}]],
            subplot_titles=("Transactions by tenure", "Median price by tenure"),
        )
        fig.add_trace(
            go.Pie(
                labels=grouped["estate_type"],
                values=grouped["count"],
                hole=0.55,
                name="Tenure",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Bar(
                x=grouped["estate_type"],
                y=grouped["median"],
                marker_color="#2ecc71",
                name="Median £",
            ),
            row=1,
            col=2,
        )
        fig.update_layout(
            title=dict(text="<b>TENURE MIX</b>", x=0.5),
            showlegend=False,
        )
        fig.update_yaxes(title_text="Median sale price (£)", row=1, col=2)
        return fig

    def plot_monthly_volume(self) -> go.Figure:
        df = self.clean_df()
        fig = go.Figure()
        if df.empty:
            return fig.update_layout(title=dict(text="<b>MONTHLY TRANSACTION VOLUME</b>", x=0.5))

        monthly = (
            df.dropna(subset=["date"])
            .assign(month=lambda d: d["date"].dt.to_period("M").dt.to_timestamp())
            .groupby("month", as_index=False)
            .size()
            .rename(columns={"size": "count"})
            .sort_values("month")
        )
        fig.add_trace(
            go.Bar(
                x=monthly["month"],
                y=monthly["count"],
                marker_color="#3498db",
                name="Transactions",
            )
        )
        fig.update_layout(
            title=dict(text="<b>MONTHLY TRANSACTION VOLUME</b>", x=0.5),
            xaxis_title="Month",
            yaxis_title="Transactions",
            bargap=0.1,
        )
        return fig

    def plot_transaction_distribution(self):
        results_df = self.clean_df()
        cat_plots.df = (
            results_df.assign(paon=results_df["paon"].astype(object))
            .groupby("paon", as_index=False)["paon"]
            .value_counts()
        )
        fig = cat_plots.plot_2_dimensional_data("Bar", x_var="paon", y_var="count")
        fig.update_xaxes(type="category")
        return cat_plots._update_layout(fig, plot_title="Transaction Distribution by Property Number")
