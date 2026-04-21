from __future__ import annotations

from urllib.parse import parse_qs, urlencode

import dash
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update

from ukhpi.dashboard.annotations import apply_historical_events
from ukhpi.dashboard.components import build_kpi_row, chart_card, postcode_tab_layout, render_postcode_content
from ukhpi.dashboard.tabs import (
    DEFAULT_GEO_LEVEL,
    DEFAULT_MAP_METRIC,
    DEFAULT_PERIOD_MODE,
    DEFAULT_VIEW,
    GEO_LEVELS,
    MAX_COMPARE_REGIONS,
    MONTH_OPTIONS,
    PERIOD_MODE_OPTIONS,
    VIEW_CONFIG,
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


def _category_view(tab_slug: str, annotations_on: bool = True) -> html.Div:
    plots = VIEW_CONFIG[tab_slug]["plots"]
    header_children: list = []
    if tab_slug == "annual_change":
        header_children.append(
            dmc.SegmentedControl(
                id="period-mode",
                data=PERIOD_MODE_OPTIONS,
                value=DEFAULT_PERIOD_MODE,
                size="sm",
            )
        )
    cards = [chart_card(view=tab_slug, method=method, label=label) for label, method in plots.items()]
    view_body = [
        html.Div(
            className="canvas",
            style={"padding": "16px 20px"},
            children=dmc.SimpleGrid(cols={"base": 1, "md": 2}, spacing="md", children=cards),
        ),
    ]
    if header_children:
        view_body.insert(
            0,
            html.Div(
                style={
                    "padding": "12px 24px",
                    "background": "rgba(52, 73, 94, 0.9)",
                    "borderBottom": "2px solid #3498db",
                },
                children=[dmc.Group(align="center", gap="md", children=header_children)],
            ),
        )
    # annotations_on stays in scope for the Store; the toolbar Switch reflects it globally.
    _ = annotations_on
    return html.Div(className="graph-container", children=view_body)


def _compose_figure(
    region: str,
    method_name: str,
    start: int,
    end: int,
    theme: str | None,
    compare_on: bool,
    compare_list: list | None,
    annotations_on: bool,
):
    fig = _build_figure(region, method_name, start, end)
    for trace in fig.data:
        trace.name = _prettify_trace_name(getattr(trace, "name", "") or "")
    extra_regions = [r for r in (compare_list or []) if r and r != region] if compare_on else []
    if extra_regions:
        for trace in fig.data:
            trace.name = f"{_region_label(region)} · {trace.name}"
        for extra in extra_regions[:MAX_COMPARE_REGIONS]:
            extra_fig = _build_figure(extra, method_name, start, end)
            for trace in extra_fig.data:
                trace.name = f"{_region_label(extra)} · {_prettify_trace_name(trace.name or '')}"
                fig.add_trace(trace)
    fig = _apply_dashboard_theme(fig, theme=theme or "dark", window=(start, end))
    return apply_historical_events(fig, enabled=bool(annotations_on), window=(start, end))


def _resolve_method(view: str, method_name: str, period_mode: str | None) -> str:
    if view == "annual_change" and period_mode == "period":
        return method_name.replace("percentage_annual_change", "percentage_change")
    return method_name


def _method_label(view: str, method_name: str) -> str:
    for label, m in VIEW_CONFIG.get(view, {}).get("plots", {}).items():
        if m == method_name or method_name.endswith(m.split("_by_")[-1]):
            return label
    return method_name


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


_LEGEND_PREFIXES = (
    "percentage_annual_change_",
    "percentage_change_",
    "average_price_",
    "house_price_index_",
    "sales_volume_",
)

_LEGEND_BARE_NAMES = {
    "percentage_annual_change": "All",
    "percentage_change": "All",
    "average_price": "All",
    "house_price_index": "All",
    "sales_volume": "All",
}


def _prettify_trace_name(name: str) -> str:
    if not name:
        return name
    if name in _LEGEND_BARE_NAMES:
        return _LEGEND_BARE_NAMES[name]
    stripped = name
    for prefix in _LEGEND_PREFIXES:
        if stripped.startswith(prefix):
            stripped = stripped[len(prefix):]
            break
    return stripped.replace("_", " ").strip().capitalize()


def _apply_dashboard_theme(fig, theme: str = "dark", window: tuple[int, int] | None = None):
    palette = _LIGHT if theme == "light" else _DARK
    for trace in fig.data:
        trace.name = _prettify_trace_name(getattr(trace, "name", "") or "")
    fig.update_layout(
        height=None,
        margin=dict(l=48, r=24, t=32, b=40),
        plot_bgcolor=palette["plot_bg"],
        paper_bgcolor=palette["paper_bg"],
        font=dict(color=palette["font"], size=12),
        title=dict(font=dict(size=14, color=palette["title"]), x=0.02, y=0.98, xanchor="left", yanchor="top"),
        xaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["zero"]),
        yaxis=dict(gridcolor=palette["grid"], zerolinecolor=palette["zero"]),
        legend=dict(
            bgcolor=palette["legend_bg"],
            bordercolor="rgba(128, 128, 128, 0.5)",
            borderwidth=1,
            title_text="",
        ),
    )
    if window is not None and _is_time_axis(fig):
        start_ts = pd.Timestamp(year=window[0], month=1, day=1)
        end_ts = pd.Timestamp(year=window[1], month=12, day=31)
        fig.update_xaxes(range=[start_ts, end_ts])
    return fig


def _is_time_axis(fig) -> bool:
    for trace in fig.data:
        x = getattr(trace, "x", None)
        if x is None or len(x) == 0:
            continue
        try:
            pd.to_datetime(x[0])
            return True
        except (ValueError, TypeError):
            return False
    return False


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
        Input("view-store", "data"),
        State("year-slider", "value"),
        State("annotations-store", "data"),
    )
    def render_tab(tab_slug: str, year_range, annotations_on):
        tab_slug = tab_slug or DEFAULT_VIEW
        if tab_slug == "map":
            end = (year_range or [None, None])[1] or 2024
            return _map_tab(default_year=end)
        if tab_slug == "postcode":
            return postcode_tab_layout()
        return _category_view(tab_slug, annotations_on=annotations_on if annotations_on is not None else True)

    @app.callback(
        Output("view-store", "data"),
        Input({"role": "view-nav", "view": dash.ALL}, "n_clicks"),
        State("view-store", "data"),
        prevent_initial_call=True,
    )
    def navigate(n_clicks_list, current):
        if not any(n_clicks_list or []):
            return no_update
        triggered = dash.callback_context.triggered_id
        if not isinstance(triggered, dict) or triggered.get("role") != "view-nav":
            return no_update
        new_view = triggered["view"]
        return no_update if new_view == current else new_view

    @app.callback(
        Output({"role": "view-nav", "view": dash.ALL}, "active"),
        Input("view-store", "data"),
        State({"role": "view-nav", "view": dash.ALL}, "id"),
    )
    def highlight_active_nav(current, ids):
        current = current or DEFAULT_VIEW
        return [nav_id["view"] == current for nav_id in ids]

    @app.callback(
        Output({"role": "grid-graph", "view": dash.MATCH, "method": dash.MATCH}, "figure"),
        Input("region-dropdown", "value"),
        Input("year-slider", "value"),
        Input("theme-store", "data"),
        Input("period-mode-store", "data"),
        Input("compare-toggle", "checked"),
        Input("compare-regions", "value"),
        Input("annotations-store", "data"),
        State({"role": "grid-graph", "view": dash.MATCH, "method": dash.MATCH}, "id"),
    )
    def update_grid_graph(region, year_range, theme, period_mode, compare_on, compare_list, annotations_on, graph_id):
        view = graph_id["view"]
        method_name = _resolve_method(view, graph_id["method"], period_mode)
        start, end = year_range
        return _compose_figure(region, method_name, start, end, theme, compare_on, compare_list, annotations_on)

    @app.callback(
        Output("chart-modal", "opened"),
        Output("modal-graph", "figure"),
        Output("chart-modal", "title"),
        Input({"role": "grid-graph-card", "view": dash.ALL, "method": dash.ALL}, "n_clicks"),
        State("region-dropdown", "value"),
        State("year-slider", "value"),
        State("theme-store", "data"),
        State("period-mode-store", "data"),
        State("compare-toggle", "checked"),
        State("compare-regions", "value"),
        State("annotations-store", "data"),
        prevent_initial_call=True,
    )
    def open_chart_modal(card_clicks, region, year_range, theme, period_mode, compare_on, compare_list, annotations_on):
        if not any(card_clicks or []):
            return no_update, no_update, no_update
        triggered = dash.callback_context.triggered_id
        if not isinstance(triggered, dict) or triggered.get("role") != "grid-graph-card":
            return no_update, no_update, no_update
        view = triggered["view"]
        method_name = _resolve_method(view, triggered["method"], period_mode)
        start, end = year_range
        fig = _compose_figure(region, method_name, start, end, theme, compare_on, compare_list, annotations_on)
        title = f"{VIEW_CONFIG[view]['label']} · {_method_label(view, triggered['method'])}"
        return True, fig, title

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
        Output("annotations-toggle", "checked"),
        Input("url", "pathname"),
        State("annotations-store", "data"),
    )
    def hydrate_annotations_toggle(_pathname, stored):
        return True if stored is None else bool(stored)

    @app.callback(
        Output("compare-regions-wrapper", "style"),
        Input("compare-toggle", "checked"),
    )
    def toggle_compare_visibility(checked):
        return {"display": "block", "marginTop": "8px"} if checked else {"display": "none"}

    @app.callback(
        Output("download-csv", "data"),
        Input("download-csv-btn", "n_clicks"),
        State("region-dropdown", "value"),
        State("year-slider", "value"),
        State("compare-toggle", "checked"),
        State("compare-regions", "value"),
        prevent_initial_call=True,
    )
    def export_csv(n_clicks, region, year_range, compare_on, compare_list):
        if not n_clicks:
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
        Output("view-store", "data", allow_duplicate=True),
        Input("url", "search"),
        State("region-dropdown", "value"),
        State("year-slider", "value"),
        State("view-store", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def load_url_state(search, cur_region, cur_year, cur_view):
        if not search:
            return no_update, no_update, no_update
        params = parse_qs(search.lstrip("?"))
        region = params.get("region", [None])[0]
        start = params.get("start", [None])[0]
        end = params.get("end", [None])[0]
        view = params.get("view", [None])[0]

        region_out = region if region and region != cur_region else no_update
        try:
            year_out = [int(start), int(end)] if start and end and [int(start), int(end)] != cur_year else no_update
        except ValueError:
            year_out = no_update
        view_out = view if view and view in VIEW_CONFIG and view != cur_view else no_update
        return region_out, year_out, view_out

    @app.callback(
        Output("url", "search"),
        Input("region-dropdown", "value"),
        Input("year-slider", "value"),
        Input("view-store", "data"),
        prevent_initial_call=True,
    )
    def save_url_state(region, year_range, view):
        start, end = year_range or [None, None]
        query = {"region": region, "start": start, "end": end, "view": view}
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
        Input("postcode-category-filter", "value"),
        State("postcode-input", "value"),
        State("theme-store", "data"),
        prevent_initial_call=True,
    )
    def fetch_postcode(_n, _submit, category_filter, postcode, theme):
        def _theme(fig):
            return _apply_dashboard_theme(fig, theme=theme or "dark")

        return render_postcode_content(postcode, _theme, category_filter or "standard")

    @app.callback(
        Output("postcode-download-csv", "data"),
        Input("postcode-download-btn", "n_clicks"),
        State("postcode-input", "value"),
        State("postcode-category-filter", "value"),
        prevent_initial_call=True,
    )
    def export_postcode_csv(n_clicks, postcode, category_filter):
        from ukhpi.core.ppi import PricePaidData
        from ukhpi.dashboard.components.postcode import _filter_by_category

        if not n_clicks or not postcode or not postcode.strip():
            return no_update
        pc = postcode.strip().upper()
        try:
            df = PricePaidData(pc).clean_df()
        except Exception:
            return no_update
        if df.empty:
            return no_update
        scoped = _filter_by_category(df, category_filter or "standard")
        out = scoped if not scoped.empty else df
        filename = f"ppd_{pc.replace(' ', '')}_{category_filter or 'all'}.csv"
        return dcc.send_data_frame(out.to_csv, filename, index=False)

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
