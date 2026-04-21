from __future__ import annotations

import dash_mantine_components as dmc
import pandas as pd
from dash import dash_table, dcc, html

from ukhpi.core.ppi import PricePaidDataPlots
from ukhpi.dashboard.components.kpi_card import kpi_card
from ukhpi.plotting.categories import PostProcess, go

CATEGORY_OPTIONS = [
    {"label": "All", "value": "all"},
    {"label": "Standard only", "value": "standard"},
    {"label": "Additional only", "value": "additional"},
]
DEFAULT_CATEGORY_FILTER = "standard"

_STANDARD_LABEL = "Standard price paid transaction"
_ADDITIONAL_LABEL = "Additional price paid transaction"


def postcode_tab_layout() -> html.Div:
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
                        align="flex-end",
                        gap="md",
                        children=[
                            dmc.TextInput(
                                id="postcode-input",
                                label="Postcode",
                                placeholder="e.g. SW1A 1AA",
                                w=220,
                            ),
                            dmc.Button(
                                "Fetch transactions",
                                id="postcode-fetch-btn",
                                color="blue",
                                variant="filled",
                            ),
                            dmc.SegmentedControl(
                                id="postcode-category-filter",
                                data=CATEGORY_OPTIONS,
                                value=DEFAULT_CATEGORY_FILTER,
                                size="sm",
                            ),
                            dmc.Button(
                                "⬇ Download CSV",
                                id="postcode-download-btn",
                                size="sm",
                                variant="light",
                                color="blue",
                            ),
                            dmc.Text(
                                "Live Land Registry query — first fetch for a postcode may take a few seconds.",
                                size="xs",
                                c="dimmed",
                            ),
                        ],
                    ),
                ],
            ),
            dcc.Download(id="postcode-download-csv"),
            dcc.Loading(
                id="postcode-loading",
                type="default",
                color="#3498db",
                children=html.Div(
                    id="postcode-content",
                    style={"padding": "20px 30px", "display": "flex", "flexDirection": "column", "gap": "20px"},
                ),
            ),
        ],
    )


def _filter_by_category(df: pd.DataFrame, category_filter: str) -> pd.DataFrame:
    if "category" not in df.columns or category_filter == "all":
        return df
    if category_filter == "additional":
        return df.loc[df["category"] == _ADDITIONAL_LABEL]
    return df.loc[df["category"] == _STANDARD_LABEL]


def _kpi_row(df: pd.DataFrame) -> dmc.SimpleGrid:
    count = len(df)
    total = df["amount"].sum() if count else 0
    mean = df["amount"].mean() if count else 0
    median = df["amount"].median() if count else 0
    if count:
        latest_row = df.sort_values("date").iloc[-1]
        latest_price = latest_row["amount"]
        latest_date = pd.to_datetime(latest_row["date"]).strftime("%b %Y")
    else:
        latest_price = 0
        latest_date = "—"

    cards = [
        kpi_card("Transactions", f"{count:,}"),
        kpi_card("Total value", f"£{PostProcess.make_number_readable(total)}"),
        kpi_card("Mean price", f"£{PostProcess.make_number_readable(mean)}"),
        kpi_card("Median price", f"£{PostProcess.make_number_readable(median)}"),
        kpi_card("Latest sale", f"£{PostProcess.make_number_readable(latest_price)}", sublabel=latest_date),
    ]
    return dmc.SimpleGrid(cols={"base": 1, "sm": 2, "md": 5}, spacing="md", children=cards)


def _recent_transactions_table(df: pd.DataFrame, limit: int = 20) -> dash_table.DataTable:
    recent = df.sort_values("date", ascending=False).head(limit).copy()
    recent["date"] = pd.to_datetime(recent["date"]).dt.strftime("%Y-%m-%d")
    recent["amount"] = recent["amount"].map(lambda v: f"£{v:,.0f}" if pd.notna(v) else "")
    cols = [c for c in ["date", "address", "amount", "property_type", "category"] if c in recent.columns]
    recent = recent[cols]
    return dash_table.DataTable(
        data=recent.to_dict("records"),
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in cols],
        style_header={"backgroundColor": "#34495e", "color": "white", "fontWeight": "700"},
        style_cell={
            "backgroundColor": "rgba(30, 30, 30, 0.95)",
            "color": "#f0f0f0",
            "padding": "8px",
            "border": "1px solid #3a3a3a",
            "fontFamily": "Segoe UI, sans-serif",
        },
        style_table={"overflowX": "auto"},
        page_size=limit,
    )


def _appreciation_table(appr: pd.DataFrame, limit: int = 10) -> dash_table.DataTable | dmc.Alert:
    if appr.empty:
        return dmc.Alert(
            "Not enough repeat sales in this postcode to compute appreciation.",
            color="gray",
            variant="light",
        )
    top = appr.head(limit).copy()
    for col in ("first_date", "last_date"):
        if col in top.columns:
            top[col] = pd.to_datetime(top[col]).dt.strftime("%Y-%m-%d")
    for col in ("p_start", "p_end", "price_change"):
        if col in top.columns:
            top[col] = top[col].map(lambda v: f"£{v:,.0f}" if pd.notna(v) else "")
    if "hold_years" in top.columns:
        top["hold_years"] = top["hold_years"].map(lambda v: f"{v:.1f}" if pd.notna(v) else "")
    if "cagr_pct" in top.columns:
        top["cagr_pct"] = top["cagr_pct"].map(lambda v: f"{v:+.1f}%" if pd.notna(v) else "")

    column_order = [
        c
        for c in (
            "address",
            "first_date",
            "last_date",
            "hold_years",
            "p_start",
            "p_end",
            "price_change",
            "cagr_pct",
        )
        if c in top.columns
    ]
    top = top[column_order]

    pretty = {
        "p_start": "First sale £",
        "p_end": "Latest sale £",
        "price_change": "Δ £",
        "cagr_pct": "CAGR",
        "hold_years": "Years held",
        "first_date": "First date",
        "last_date": "Latest date",
    }
    return dash_table.DataTable(
        data=top.to_dict("records"),
        columns=[{"name": pretty.get(c, c.replace("_", " ").title()), "id": c} for c in column_order],
        style_header={"backgroundColor": "#34495e", "color": "white", "fontWeight": "700"},
        style_cell={
            "backgroundColor": "rgba(30, 30, 30, 0.95)",
            "color": "#f0f0f0",
            "padding": "8px",
            "border": "1px solid #3a3a3a",
        },
        style_table={"overflowX": "auto"},
        page_size=limit,
    )


def _graph_card(fig: go.Figure, graph_id: str, title: str, height: str = "400px") -> html.Div:
    return html.Div(
        className="chart-card",
        children=dmc.Card(
            withBorder=True,
            radius="md",
            padding="sm",
            children=[
                dmc.Text(title, size="sm", fw=600, c="gray.3", mb=4),
                dcc.Graph(
                    id=graph_id,
                    figure=fig,
                    config={
                        "displayModeBar": False,
                        "displaylogo": False,
                    },
                    style={"height": height},
                ),
            ],
        ),
    )


def _safe_plot(fn, theme_fn, fallback_text: str) -> go.Figure:
    try:
        return theme_fn(fn())
    except Exception as exc:
        return go.Figure().add_annotation(text=f"{fallback_text}: {exc}", showarrow=False)


def render_postcode_content(
    postcode: str | None,
    theme_fn,
    category_filter: str = DEFAULT_CATEGORY_FILTER,
) -> list:
    """Render the full postcode detail view. `theme_fn` applies a figure theme."""
    if not postcode or not postcode.strip():
        return [dmc.Alert("Enter a postcode above and click Fetch transactions.", color="yellow", variant="light")]

    pc = postcode.strip().upper()
    try:
        ppd = PricePaidDataPlots(pc)
        full_df = ppd.clean_df()
    except Exception as exc:  # live SPARQL / cache read failures
        return [dmc.Alert(f"Could not fetch postcode data: {exc}", color="red", variant="light")]

    if full_df.empty:
        return [dmc.Alert(f"No transactions found for {pc}.", color="yellow", variant="light")]

    scoped_df = _filter_by_category(full_df, category_filter)
    if scoped_df.empty:
        scope_note = dmc.Alert(
            f"No {category_filter} transactions for {pc} — try a different scope.",
            color="yellow",
            variant="light",
        )
    else:
        scope_note = None

    fig_timeline = _safe_plot(ppd.plot_price_timeline, theme_fn, "Price timeline unavailable")
    fig_dist = _safe_plot(ppd.plot_price_distribution, theme_fn, "Price distribution unavailable")
    fig_type_med = _safe_plot(ppd.plot_property_type_medians, theme_fn, "Property-type medians unavailable")
    fig_tenure = _safe_plot(ppd.plot_tenure_mix, theme_fn, "Tenure mix unavailable")
    fig_volume = _safe_plot(ppd.plot_monthly_volume, theme_fn, "Monthly volume unavailable")

    try:
        appr = ppd.calculate_appreciated_prices()
    except Exception:
        appr = pd.DataFrame()

    kpi_source = scoped_df if not scoped_df.empty else full_df
    body: list = [
        dmc.Title(f"🏠 {pc}", order=3, c="gray.3"),
    ]
    if scope_note is not None:
        body.append(scope_note)
    body.extend(
        [
            _kpi_row(kpi_source),
            _graph_card(fig_timeline, "postcode-timeline-graph", "Price over time", height="420px"),
            dmc.SimpleGrid(
                cols={"base": 1, "md": 2},
                spacing="md",
                children=[
                    _graph_card(fig_dist, "postcode-dist-graph", "Price distribution"),
                    _graph_card(fig_type_med, "postcode-type-medians-graph", "Median price by property type"),
                    _graph_card(fig_tenure, "postcode-tenure-graph", "Tenure mix"),
                    _graph_card(fig_volume, "postcode-volume-graph", "Monthly transaction volume"),
                ],
            ),
            dmc.Title("Recent transactions", order=5, c="gray.4"),
            _recent_transactions_table(scoped_df if not scoped_df.empty else full_df),
            dmc.Title("Repeat sales — CAGR", order=5, c="gray.4"),
            _appreciation_table(appr),
        ]
    )
    return body
