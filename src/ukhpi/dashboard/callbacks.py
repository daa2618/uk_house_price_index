from __future__ import annotations

from urllib.parse import parse_qs, urlencode

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update

from ukhpi.dashboard.annotations import apply_historical_events
from ukhpi.dashboard.components import build_kpi_row, postcode_tab_layout, render_postcode_content
from ukhpi.dashboard.tabs import (
    DEFAULT_GEO_LEVEL,
    DEFAULT_MAP_METRIC,
    DEFAULT_PERIOD_MODE,
    GEO_LEVELS,
    MAX_COMPARE_REGIONS,
    MONTH_OPTIONS,
    PERIOD_MODE_OPTIONS,
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


def _region_label(region: str | None) -> str:
    if not region:
        return ""
    return region.replace("-", " ").title()


def _build_figure(region: str, method_name: str, start: int, end: int):
    hpi = HousePriceIndexPlots(start_year=start, end_year=end, region=region)
    return getattr(hpi, method_name)()


def _plot_selector(tab_slug: str, annotations_on: bool = True) -> html.Div:
    plots = TAB_CONFIG[tab_slug]["plots"]
    header_children = [
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
    ]
    if tab_slug == "annual_change":
        header_children.append(
            dmc.SegmentedControl(
                id="period-mode",
                data=PERIOD_MODE_OPTIONS,
                value=DEFAULT_PERIOD_MODE,
                size="sm",
            )
        )
    header_children.append(
        dmc.Switch(
            id="annotations-toggle",
            label="Historical events",
            checked=bool(annotations_on),
            size="sm",
        )
    )
    header_children.append(
        dmc.Button(
            "⬇ Download CSV",
            id={"role": "download-csv-btn", "tab": tab_slug},
            size="sm",
            variant="light",
            color="blue",
        )
    )
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
                        style={"display": "flex", "alignItems": "center", "gap": "15px", "flexWrap": "wrap"},
                        children=header_children,
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
        State("annotations-store", "data"),
    )
    def render_tab(tab_slug: str, year_range, annotations_on):
        if tab_slug == "map":
            end = (year_range or [None, None])[1] or 2024
            return _map_tab(default_year=end)
        if tab_slug == "postcode":
            return postcode_tab_layout()
        return _plot_selector(tab_slug, annotations_on=annotations_on if annotations_on is not None else True)

    @app.callback(
        Output({"role": "graph", "tab": dash.MATCH}, "figure"),
        Input("region-dropdown", "value"),
        Input({"role": "plot-dropdown", "tab": dash.MATCH}, "value"),
        Input("year-slider", "value"),
        Input("theme-store", "data"),
        Input("period-mode-store", "data"),
        Input("compare-toggle", "checked"),
        Input("compare-regions", "value"),
        Input("annotations-store", "data"),
        State({"role": "plot-dropdown", "tab": dash.MATCH}, "id"),
        prevent_initial_call="initial_duplicate",
    )
    def update_graph(
        region, plot_choice, year_range, theme, period_mode, compare_on, compare_list, annotations_on, dropdown_id
    ):
        tab_slug = dropdown_id["tab"]
        method_name = TAB_CONFIG[tab_slug]["plots"][plot_choice]
        if tab_slug == "annual_change" and period_mode == "period":
            method_name = method_name.replace("percentage_annual_change", "percentage_change")
        start, end = year_range
        fig = _build_figure(region, method_name, start, end)

        extra_regions = [r for r in (compare_list or []) if r and r != region] if compare_on else []
        if extra_regions:
            for trace in fig.data:
                trace.name = f"{_region_label(region)} · {trace.name}"
            for extra in extra_regions[:MAX_COMPARE_REGIONS]:
                extra_fig = _build_figure(extra, method_name, start, end)
                for trace in extra_fig.data:
                    trace.name = f"{_region_label(extra)} · {trace.name}"
                    fig.add_trace(trace)
        fig = _apply_dashboard_theme(fig, theme=theme or "dark")
        return apply_historical_events(fig, enabled=bool(annotations_on))

    @app.callback(
        Output("period-mode-store", "data"),
        Input("period-mode", "value"),
        prevent_initial_call=True,
    )
    def sync_period_mode(value):
        return value or DEFAULT_PERIOD_MODE

    @app.callback(
        Output("annotations-store", "data"),
        Input("annotations-toggle", "checked"),
        prevent_initial_call=True,
    )
    def sync_annotations(checked):
        return bool(checked)

    @app.callback(
        Output("compare-regions-wrapper", "style"),
        Input("compare-toggle", "checked"),
    )
    def toggle_compare_visibility(checked):
        return {"display": "block", "marginTop": "8px"} if checked else {"display": "none"}

    @app.callback(
        Output("download-csv", "data"),
        Input({"role": "download-csv-btn", "tab": dash.ALL}, "n_clicks"),
        State("region-dropdown", "value"),
        State("year-slider", "value"),
        State("compare-toggle", "checked"),
        State("compare-regions", "value"),
        prevent_initial_call=True,
    )
    def export_csv(n_clicks_list, region, year_range, compare_on, compare_list):
        if not any(n_clicks_list or []):
            return no_update
        start, end = year_range
        regions = [region]
        if compare_on:
            regions.extend(r for r in (compare_list or []) if r and r != region)
        frames = []
        for r in regions:
            df = HousePriceIndexPlots(start_year=start, end_year=end, region=r).hpi_df.copy()
            if df.empty:
                continue
            df.insert(0, "region", r)
            frames.append(df)
        if not frames:
            return no_update
        combined = pd.concat(frames, ignore_index=True)
        filename = f"ukhpi_{'-'.join(regions)}_{start}_{end}.csv"
        return dcc.send_data_frame(combined.to_csv, filename, index=False)

    @app.callback(
        Output("region-dropdown", "value", allow_duplicate=True),
        Output("year-slider", "value", allow_duplicate=True),
        Output("tabs", "value", allow_duplicate=True),
        Input("url", "search"),
        State("region-dropdown", "value"),
        State("year-slider", "value"),
        State("tabs", "value"),
        prevent_initial_call="initial_duplicate",
    )
    def load_url_state(search, cur_region, cur_year, cur_tab):
        if not search:
            return no_update, no_update, no_update
        params = parse_qs(search.lstrip("?"))
        region = params.get("region", [None])[0]
        start = params.get("start", [None])[0]
        end = params.get("end", [None])[0]
        tab = params.get("tab", [None])[0]

        region_out = region if region and region != cur_region else no_update
        try:
            year_out = [int(start), int(end)] if start and end and [int(start), int(end)] != cur_year else no_update
        except ValueError:
            year_out = no_update
        tab_out = tab if tab and tab in TAB_CONFIG and tab != cur_tab else no_update
        return region_out, year_out, tab_out

    @app.callback(
        Output("url", "search"),
        Input("region-dropdown", "value"),
        Input("year-slider", "value"),
        Input("tabs", "value"),
        prevent_initial_call=True,
    )
    def save_url_state(region, year_range, tab):
        start, end = year_range or [None, None]
        query = {"region": region, "start": start, "end": end, "tab": tab}
        query = {k: v for k, v in query.items() if v is not None}
        return "?" + urlencode(query) if query else ""

    @app.callback(
        Output("compare-regions", "value"),
        Input("compare-regions", "value"),
        Input("region-dropdown", "value"),
        prevent_initial_call=True,
    )
    def enforce_compare_constraints(current, primary):
        filtered = [v for v in (current or []) if v and v != primary][:MAX_COMPARE_REGIONS]
        if filtered == (current or []):
            return no_update
        return filtered

    @app.callback(
        Output("postcode-content", "children"),
        Input("postcode-fetch-btn", "n_clicks"),
        Input("postcode-input", "n_submit"),
        State("postcode-input", "value"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def fetch_postcode(_n, _submit, postcode, theme):
        def _theme(fig):
            return _apply_dashboard_theme(fig, theme=theme or "dark")

        return render_postcode_content(postcode, _theme)

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
