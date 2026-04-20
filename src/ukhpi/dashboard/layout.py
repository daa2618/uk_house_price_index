from __future__ import annotations

import dash_mantine_components as dmc
from dash import dcc, html

from ukhpi.core.sparql import SparqlQuery
from ukhpi.dashboard.components import build_region_options, control_group
from ukhpi.dashboard.tabs import (
    DEFAULT_END,
    DEFAULT_PERIOD_MODE,
    DEFAULT_REGION,
    DEFAULT_START,
    DEFAULT_TAB,
    HPI_MAX_YEAR,
    HPI_MIN_YEAR,
    MAX_COMPARE_REGIONS,
    TAB_CONFIG,
)

_regions_df = SparqlQuery().HPI_REGIONS
REGION_OPTIONS = build_region_options(_regions_df)


def _theme_toggle() -> dmc.ActionIcon:
    return dmc.ActionIcon(
        children="🌙",
        id="theme-toggle",
        variant="filled",
        color="dark",
        size="lg",
        radius="xl",
    )


def _header() -> html.Div:
    return html.Div(
        className="header-section",
        children=[
            html.Div(
                style={"display": "flex", "alignItems": "center", "justifyContent": "space-between"},
                children=[
                    html.Div(style={"width": "48px"}),
                    html.Div(
                        children=[
                            html.H1(
                                "🏘️ UK House Price Index Dashboard",
                                style={
                                    "textAlign": "center",
                                    "color": "white",
                                    "margin": "0",
                                    "fontSize": "2.5em",
                                    "fontWeight": "700",
                                    "textShadow": "2px 2px 4px rgba(0,0,0,0.5)",
                                },
                            ),
                            html.P(
                                "Interactive visualization of UK housing market trends and statistics",
                                style={
                                    "textAlign": "center",
                                    "color": "#ecf0f1",
                                    "margin": "10px 0 0 0",
                                    "fontSize": "1.1em",
                                    "fontWeight": "300",
                                },
                            ),
                        ],
                    ),
                    _theme_toggle(),
                ],
            ),
        ],
    )


def _slider_marks() -> dict[int, dict]:
    step = 5
    years = list(range(HPI_MIN_YEAR, HPI_MAX_YEAR + 1, step))
    if years[-1] != HPI_MAX_YEAR:
        years.append(HPI_MAX_YEAR)
    return {y: {"label": str(y), "style": {"color": "#f0f0f0", "fontSize": "12px"}} for y in years}


def _controls() -> html.Div:
    region_dropdown = dcc.Dropdown(
        id="region-dropdown",
        options=REGION_OPTIONS,
        value=DEFAULT_REGION,
        clearable=False,
        searchable=True,
        style={"minWidth": "200px"},
    )
    compare_toggle = dmc.Switch(
        id="compare-toggle",
        label="Compare regions",
        checked=False,
        size="sm",
        mt=6,
    )
    compare_dropdown = html.Div(
        id="compare-regions-wrapper",
        style={"display": "none", "marginTop": "8px"},
        children=dcc.Dropdown(
            id="compare-regions",
            options=REGION_OPTIONS,
            multi=True,
            value=[],
            placeholder=f"Add up to {MAX_COMPARE_REGIONS} regions",
            style={"minWidth": "250px"},
        ),
    )
    region_group = html.Div(children=[region_dropdown, compare_toggle, compare_dropdown])
    year_slider = dcc.RangeSlider(
        id="year-slider",
        min=HPI_MIN_YEAR,
        max=HPI_MAX_YEAR,
        step=1,
        value=[DEFAULT_START, DEFAULT_END],
        marks=_slider_marks(),
        tooltip={"placement": "bottom", "always_visible": True},
        allowCross=False,
    )
    return html.Div(
        className="controls-section",
        children=[
            html.Div(
                style={"display": "flex", "flexWrap": "wrap", "gap": "20px", "alignItems": "flex-end"},
                className="controls-row",
                children=[
                    control_group("Select Region", region_group, flex="1", min_width="250px"),
                    control_group("Year Range", year_slider, flex="2", min_width="300px"),
                ],
            )
        ],
    )


def _kpi_section() -> html.Div:
    return html.Div(
        style={"padding": "16px 30px", "background": "rgba(42, 42, 42, 0.95)", "borderBottom": "1px solid #444"},
        children=[
            dcc.Loading(
                id="kpi-loading",
                type="dot",
                color="#3498db",
                children=html.Div(id="kpi-row"),
            )
        ],
    )


def _tabs() -> html.Div:
    return html.Div(
        style={"padding": "0 30px", "background": "rgba(42, 42, 42, 0.95)"},
        children=[
            dcc.Tabs(
                id="tabs",
                value=DEFAULT_TAB,
                children=[dcc.Tab(label=cfg["label"], value=slug, className="tab") for slug, cfg in TAB_CONFIG.items()],
                style={"marginBottom": "0"},
            )
        ],
    )


def build_layout() -> dmc.MantineProvider:
    return dmc.MantineProvider(
        id="mantine-provider",
        forceColorScheme="dark",
        children=html.Div(
            className="main-container",
            children=[
                dcc.Location(id="url", refresh=False),
                dcc.Store(id="theme-store", storage_type="local", data="dark"),
                dcc.Store(id="period-mode-store", data=DEFAULT_PERIOD_MODE),
                dcc.Store(id="annotations-store", storage_type="local", data=True),
                dcc.Download(id="download-csv"),
                _header(),
                _controls(),
                _kpi_section(),
                _tabs(),
                html.Div(id="tab-content", className="content-section"),
            ],
        ),
    )
