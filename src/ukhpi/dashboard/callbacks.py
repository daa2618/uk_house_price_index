from __future__ import annotations

import dash
import dash_mantine_components as dmc
from dash import Input, Output, State, dcc, html, no_update

from ukhpi.dashboard.components import build_kpi_row
from ukhpi.dashboard.tabs import (
    DEFAULT_GEO_LEVEL,
    DEFAULT_MAP_METRIC,
    GEO_LEVELS,
    MONTH_OPTIONS,
    TAB_CONFIG,
)
from ukhpi.geo.ops import GeoOps
from ukhpi.plotting.hpi_plots import HousePriceIndexPlots

_DARK = {
    "plot_bg": "rgba(30, 30, 30, 0.9)",
    "paper_bg": "rgba(30, 30, 30, 0.9)",
    "font": "#f0f0f0",
    "title": "#ecf0f1",
    "grid": "rgba(128, 128, 128, 0.3)",
    "zero": "rgba(128, 128, 128, 0.5)",
    "legend_bg": "rgba(42, 42, 42, 0.8)",
}
_LIGHT = {
    "plot_bg": "rgba(255, 255, 255, 0.95)",
    "paper_bg": "rgba(245, 247, 250, 0.95)",
    "font": "#212529",
    "title": "#212529",
    "grid": "rgba(180, 180, 180, 0.4)",
    "zero": "rgba(120, 120, 120, 0.6)",
    "legend_bg": "rgba(255, 255, 255, 0.85)",
}

_geo_ops = GeoOps()
_geo_year_range: tuple[int, int] | None = None


def _get_geo_ops(start: int, end: int) -> GeoOps:
    """Module-level GeoOps with cache reset whenever the year window changes."""
    global _geo_year_range
    if _geo_year_range != (start, end):
        _geo_ops.hpi_by_geo_dict.clear()
        _geo_year_range = (start, end)
    return _geo_ops


def _plot_selector(tab_slug: str) -> html.Div:
    plots = TAB_CONFIG[tab_slug]["plots"]
    return html.Div(
        className="graph-container",
        children=[
            html.Div(
                style={
                    "padding": "20px 30px",
                    "background": "rgba(52, 73, 94, 0.9)",
                    "borderBottom": "2px solid #3498db",
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "15px"},
                        children=[
                            html.Label(
                                "📊 Select Visualization:",
                                style={"color": "#ecf0f1", "fontWeight": "600", "fontSize": "16px", "margin": "0"},
                            ),
                            dcc.Dropdown(
                                id={"role": "plot-dropdown", "tab": tab_slug},
                                options=[{"label": f"📈 {k}", "value": k} for k in plots.keys()],
                                value=next(iter(plots.keys())),
                                style={"minWidth": "300px", "flex": "1"},
                                clearable=False,
                            ),
                        ],
                    )
                ],
            ),
            html.Div(
                className="graph-wrapper",
                children=[
                    dcc.Loading(
                        id={"role": "loading", "tab": tab_slug},
                        type="circle",
                        color="#3498db",
                        children=[
                            dcc.Graph(
                                id={"role": "graph", "tab": tab_slug},
                                style={"height": "100%", "width": "100%"},
                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
                                    "toImageButtonOptions": {
                                        "format": "png",
                                        "filename": f"uk_housing_{tab_slug}",
                                        "height": 800,
                                        "width": 1200,
                                        "scale": 2,
                                    },
                                },
                            )
                        ],
                    )
                ],
            ),
        ],
    )


def _map_tab(default_year: int) -> html.Div:
    metric_options = [{"label": col.replace("_", " ").title(), "value": col} for col in _geo_ops.numeric_cols]
    return html.Div(
        className="graph-container",
        children=[
            html.Div(
                style={
                    "padding": "20px 30px",
                    "background": "rgba(52, 73, 94, 0.9)",
                    "borderBottom": "2px solid #3498db",
                },
                children=[
                    dmc.Group(
                        gap="md",
                        wrap="wrap",
                        children=[
                            dmc.Stack(
                                gap=4,
                                children=[
                                    dmc.Text("Geo level", size="xs", c="dimmed", fw=700),
                                    dmc.SegmentedControl(
                                        id="map-geo-level",
                                        data=GEO_LEVELS,
                                        value=DEFAULT_GEO_LEVEL,
                                        size="sm",
                                    ),
                                ],
                            ),
                            dmc.Stack(
                                gap=4,
                                style={"minWidth": "260px", "flex": "1"},
                                children=[
                                    dmc.Text("Metric", size="xs", c="dimmed", fw=700),
                                    dcc.Dropdown(
                                        id="map-metric",
                                        options=metric_options,
                                        value=DEFAULT_MAP_METRIC,
                                        clearable=False,
                                        searchable=True,
                                    ),
                                ],
                            ),
                            dmc.Stack(
                                gap=4,
                                children=[
                                    dmc.Text("Reference month", size="xs", c="dimmed", fw=700),
                                    dmc.Select(
                                        id="map-month",
                                        data=MONTH_OPTIONS,
                                        value="12",
                                        size="sm",
                                        w=160,
                                    ),
                                ],
                            ),
                            dmc.Stack(
                                gap=4,
                                children=[
                                    dmc.Text("Reference year", size="xs", c="dimmed", fw=700),
                                    dmc.NumberInput(
                                        id="map-year",
                                        value=default_year,
                                        min=1995,
                                        max=default_year,
                                        size="sm",
                                        w=120,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="graph-wrapper",
                children=[
                    dcc.Loading(
                        id="map-loading",
                        type="circle",
                        color="#3498db",
                        children=[
                            dcc.Graph(
                                id="map-graph",
                                style={"height": "100%", "width": "100%"},
                                config={"displaylogo": False, "scrollZoom": True},
                            )
                        ],
                    )
                ],
            ),
            html.Div(
                id="map-status",
                style={"padding": "10px 30px", "color": "#bdc3c7", "fontSize": "13px", "fontStyle": "italic"},
            ),
        ],
    )


def _apply_dashboard_theme(fig, theme: str = "dark"):
    palette = _LIGHT if theme == "light" else _DARK
    fig.update_layout(
        height=None,
        margin=dict(l=50, r=50, t=80, b=50),
        plot_bgcolor=palette["plot_bg"],
        paper_bgcolor=palette["paper_bg"],
        font=dict(color=palette["font"], size=12),
        title=dict(font=dict(size=24, color=palette["title"]), x=0.5, y=0.95),
        xaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["zero"]),
        yaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["zero"]),
        legend=dict(bgcolor=palette["legend_bg"], bordercolor="rgba(128, 128, 128, 0.5)", borderwidth=1),
    )
    return fig


def _apply_map_theme(fig, theme: str = "dark"):
    palette = _LIGHT if theme == "light" else _DARK
    fig.update_layout(
        paper_bgcolor=palette["paper_bg"],
        font=dict(color=palette["font"], size=12),
        title=dict(font=dict(size=18, color=palette["title"]), x=0.02, y=0.97),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    return fig


def register_callbacks(app: dash.Dash) -> None:
    @app.callback(
        Output("tab-content", "children"),
        Input("tabs", "value"),
        State("year-slider", "value"),
    )
    def render_tab(tab_slug: str, year_range):
        if tab_slug == "map":
            end = (year_range or [None, None])[1] or 2024
            return _map_tab(default_year=end)
        return _plot_selector(tab_slug)

    @app.callback(
        Output({"role": "graph", "tab": dash.MATCH}, "figure"),
        Input("region-dropdown", "value"),
        Input({"role": "plot-dropdown", "tab": dash.MATCH}, "value"),
        Input("year-slider", "value"),
        Input("theme-store", "data"),
        State({"role": "plot-dropdown", "tab": dash.MATCH}, "id"),
        prevent_initial_call="initial_duplicate",
    )
    def update_graph(region, plot_choice, year_range, theme, dropdown_id):
        tab_slug = dropdown_id["tab"]
        method_name = TAB_CONFIG[tab_slug]["plots"][plot_choice]
        start, end = year_range
        hpi_plots = HousePriceIndexPlots(start_year=start, end_year=end, region=region)
        fig = getattr(hpi_plots, method_name)()
        return _apply_dashboard_theme(fig, theme=theme or "dark")

    @app.callback(
        Output("kpi-row", "children"),
        Input("region-dropdown", "value"),
        Input("year-slider", "value"),
    )
    def update_kpi_row(region, year_range):
        start, end = year_range
        hpi = HousePriceIndexPlots(start_year=start, end_year=end, region=region)
        return build_kpi_row(hpi.hpi_df, region)

    @app.callback(
        Output("map-graph", "figure"),
        Output("map-status", "children"),
        Input("map-geo-level", "value"),
        Input("map-metric", "value"),
        Input("map-month", "value"),
        Input("map-year", "value"),
        Input("year-slider", "value"),
        Input("theme-store", "data"),
    )
    def update_map(geo_level, metric, month, year, year_range, theme):
        if not (geo_level and metric and month and year and year_range):
            return no_update, no_update
        start, end = year_range
        ref_month = f"{int(year)}-{str(month).zfill(2)}"
        try:
            ops = _get_geo_ops(int(start), int(end))
            fig = ops.plot_hpi_by_geo(
                start_year=int(start),
                end_year=int(end),
                geo_type_id=geo_level,
                ref_month=ref_month,
                metric=metric,
            )
        except Exception as exc:
            return {}, f"Could not render map: {exc}"
        fig = _apply_map_theme(fig, theme=theme or "dark")
        status = f"Showing {metric.replace('_', ' ')} by {geo_level.replace('_name', '')} for {ref_month}."
        return fig, status

    @app.callback(
        Output("region-dropdown", "value"),
        Input("map-graph", "clickData"),
        prevent_initial_call=True,
    )
    def map_click_to_region(click_data):
        if not click_data or "points" not in click_data:
            return no_update
        try:
            location = click_data["points"][0]["location"]
        except (KeyError, IndexError):
            return no_update
        return str(location).lower().replace(" ", "-")

    @app.callback(
        Output("theme-store", "data"),
        Input("theme-toggle", "n_clicks"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def click_toggle(_n, current):
        return "light" if (current or "dark") == "dark" else "dark"

    @app.callback(
        Output("mantine-provider", "forceColorScheme"),
        Output("theme-toggle", "children"),
        Input("theme-store", "data"),
    )
    def apply_theme(theme):
        scheme = theme or "dark"
        icon = "☀️" if scheme == "light" else "🌙"
        return scheme, icon
