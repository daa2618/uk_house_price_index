from __future__ import annotations

from datetime import datetime

HPI_MIN_YEAR = 1995
HPI_MAX_YEAR = datetime.now().year

TAB_CONFIG: dict[str, dict] = {
    "avg_prices": {
        "label": "📊 Average Prices",
        "plots": {
            "Average Price by Build Types": "plot_average_price_by_build_types",
            "Average Price by Occupant Types": "plot_average_price_by_occupant_types",
            "Average Price by Payment Types": "plot_average_price_by_payment_types",
            "Average Price by Property Types": "plot_average_price_by_property_types",
        },
    },
    "house_price_index": {
        "label": "📈 House Price Index",
        "plots": {
            "HPI by Build Types": "plot_house_price_index_by_build_type",
            "HPI by Occupant Types": "plot_house_price_index_by_occupant_types",
            "HPI by Payment Types": "plot_house_price_index_by_payment_types",
            "HPI by Property Types": "plot_house_price_index_by_property_types",
        },
    },
    "sales_volume": {
        "label": "📉 Sales Volume",
        "plots": {
            "Sales Volume by Build Types": "plot_sales_volume_by_build_types",
            "Sales Volume by Payment Types": "plot_sales_volume_by_payment_types",
            "Sales Volume by Property Types": "plot_sales_volume_by_property_types",
            "Cash vs Mortgage Share": "plot_sales_volume_cash_vs_mortgage",
        },
    },
    "annual_change": {
        "label": "📋 % Annual Change",
        "plots": {
            "Change by Build Types": "plot_percentage_annual_change_by_build_types",
            "Change by Occupant Types": "plot_percentage_annual_change_by_occupant_types",
            "Change by Payment Types": "plot_percentage_annual_change_by_payment_types",
            "Change by Property Types": "plot_percentage_annual_change_by_property_types",
        },
    },
    "map": {
        "label": "🗺️ Map",
        "plots": {},
    },
    "postcode": {
        "label": "🏠 Postcode",
        "plots": {},
    },
}

GEO_LEVELS = [
    {"label": "Country", "value": "ctry_name"},
    {"label": "Region", "value": "rgn_name"},
    {"label": "County / UA", "value": "ctyua_name"},
]
DEFAULT_GEO_LEVEL = "ctyua_name"

MONTH_OPTIONS = [
    {"label": "January", "value": "01"},
    {"label": "February", "value": "02"},
    {"label": "March", "value": "03"},
    {"label": "April", "value": "04"},
    {"label": "May", "value": "05"},
    {"label": "June", "value": "06"},
    {"label": "July", "value": "07"},
    {"label": "August", "value": "08"},
    {"label": "September", "value": "09"},
    {"label": "October", "value": "10"},
    {"label": "November", "value": "11"},
    {"label": "December", "value": "12"},
]
DEFAULT_MAP_METRIC = "average_price"

PERIOD_MODE_OPTIONS = [
    {"label": "Annual (YoY)", "value": "annual"},
    {"label": "Period-over-period", "value": "period"},
]
DEFAULT_PERIOD_MODE = "annual"

MAX_COMPARE_REGIONS = 3

DEFAULT_TAB = "avg_prices"
DEFAULT_REGION = "england"
DEFAULT_START = 2020
DEFAULT_END = min(2024, HPI_MAX_YEAR)
