from __future__ import annotations

import math

import dash_mantine_components as dmc
import pandas as pd

from ukhpi.plotting.categories import PostProcess

_NA = "N/A"


def _format_currency(value: float | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return _NA
    return f"£{PostProcess.make_number_readable(value)}"


def _format_count(value: float | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return _NA
    return PostProcess.make_number_readable(int(value))


def _format_pct(value: float | None) -> tuple[str, str | None]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return _NA, None
    sign = "+" if value >= 0 else ""
    color = "teal.4" if value >= 0 else "red.4"
    return f"{sign}{value:.2f}%", color


def kpi_card(label: str, value: str, sublabel: str | None = None, value_color: str | None = None) -> dmc.Card:
    value_kwargs = {"size": "xl", "fw": 700, "mt": 4}
    if value_color:
        value_kwargs["c"] = value_color
    children = [
        dmc.Text(label.upper(), size="xs", c="dimmed", fw=700, style={"letterSpacing": "0.5px"}),
        dmc.Text(value, **value_kwargs),
    ]
    if sublabel:
        children.append(dmc.Text(sublabel, size="xs", c="dimmed", mt=4))
    return dmc.Card(children=children, withBorder=True, shadow="sm", radius="md", p="md")


def build_kpi_row(hpi_df: pd.DataFrame, region: str) -> dmc.SimpleGrid:
    if hpi_df.empty or "average_price" not in hpi_df.columns:
        cards = [kpi_card("No data", _NA) for _ in range(4)]
        return dmc.SimpleGrid(cols={"base": 1, "sm": 2, "md": 4}, spacing="md", children=cards)

    df = hpi_df.sort_values("ref_period_start") if "ref_period_start" in hpi_df.columns else hpi_df
    latest = df.iloc[-1]
    earliest = df.iloc[0]
    latest_period = pd.to_datetime(latest.get("ref_period_start"), errors="coerce")
    period_label = latest_period.strftime("%b %Y") if pd.notna(latest_period) else ""
    region_label = region.replace("-", " ").title() if region else ""

    avg_price = latest.get("average_price")
    yoy_change = latest.get("percentage_annual_change")
    last_volume = latest.get("sales_volume")

    first_price = earliest.get("average_price")
    if first_price and pd.notna(first_price) and first_price != 0:
        period_change_value = (avg_price / first_price - 1) * 100
    else:
        period_change_value = None

    yoy_str, yoy_color = _format_pct(yoy_change)
    period_change_str, period_change_color = _format_pct(period_change_value)

    sub = " · ".join(x for x in [region_label, period_label] if x)

    cards = [
        kpi_card("Latest avg price", _format_currency(avg_price), sublabel=sub),
        kpi_card("YoY change", yoy_str, sublabel="vs. same month last year", value_color=yoy_color),
        kpi_card(
            "Sales volume",
            _format_count(last_volume),
            sublabel=f"{period_label} transactions" if period_label else None,
        ),
        kpi_card(
            "Period change", period_change_str, sublabel="across selected window", value_color=period_change_color
        ),
    ]
    return dmc.SimpleGrid(cols={"base": 1, "sm": 2, "md": 4}, spacing="md", children=cards)
