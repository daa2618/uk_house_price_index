from __future__ import annotations

import dash_mantine_components as dmc
import pandas as pd
from dash import dash_table, dcc, html

from ukhpi.core.ppi import PricePaidDataPlots
from ukhpi.dashboard.components.kpi_card import kpi_card
from ukhpi.plotting.categories import PostProcess, go


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
                            dmc.Text(
                                "Live Land Registry query — first fetch for a postcode may take a few seconds.",
                                size="xs",
                                c="dimmed",
                            ),
                        ],
                    ),
                ],
            ),
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


def _kpi_row(df: pd.DataFrame) -> dmc.SimpleGrid:
    count = len(df)
    total = df["amount"].sum()
    mean = df["amount"].mean()
    latest_row = df.sort_values("date").iloc[-1]
    latest_price = latest_row["amount"]
    latest_date = pd.to_datetime(latest_row["date"]).strftime("%b %Y")

    cards = [
        kpi_card("Transactions", f"{count:,}"),
        kpi_card("Total value", f"£{PostProcess.make_number_readable(total)}"),
        kpi_card("Mean price", f"£{PostProcess.make_number_readable(mean)}"),
        kpi_card("Latest sale", f"£{PostProcess.make_number_readable(latest_price)}", sublabel=latest_date),
    ]
    return dmc.SimpleGrid(cols={"base": 1, "sm": 2, "md": 4}, spacing="md", children=cards)


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
    for col in ("price_change", "appreciation_per_day", "appreciation_per_year"):
        if col in top.columns:
            top[col] = top[col].map(lambda v: f"£{v:,.2f}" if pd.notna(v) else "")
    return dash_table.DataTable(
        data=top.to_dict("records"),
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in top.columns],
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


def _graph(fig: go.Figure, graph_id: str) -> dcc.Graph:
    return dcc.Graph(
        id=graph_id,
        figure=fig,
        config={"displaylogo": False, "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]},
        style={"height": "480px"},
    )


def render_postcode_content(postcode: str | None, theme_fn) -> list:
    """Render the full postcode detail view. `theme_fn` applies a figure theme."""
    if not postcode or not postcode.strip():
        return [dmc.Alert("Enter a postcode above and click Fetch transactions.", color="yellow", variant="light")]

    pc = postcode.strip().upper()
    try:
        ppd = PricePaidDataPlots(pc)
        df = ppd.clean_df()
    except Exception as exc:  # live SPARQL / cache read failures
        return [dmc.Alert(f"Could not fetch postcode data: {exc}", color="red", variant="light")]

    if df.empty:
        return [dmc.Alert(f"No transactions found for {pc}.", color="yellow", variant="light")]

    try:
        fig_types = theme_fn(ppd.plot_property_types())
    except Exception as exc:
        fig_types = go.Figure().add_annotation(text=f"Property-type plot unavailable: {exc}", showarrow=False)
    try:
        fig_tx = theme_fn(ppd.plot_transaction_distribution())
    except Exception as exc:
        fig_tx = go.Figure().add_annotation(text=f"Transaction-distribution plot unavailable: {exc}", showarrow=False)

    try:
        appr = ppd.calculate_appreciated_prices()
    except Exception:
        appr = pd.DataFrame()

    return [
        dmc.Title(f"🏠 {pc}", order=3, c="gray.3"),
        _kpi_row(df),
        dmc.SimpleGrid(
            cols={"base": 1, "md": 2},
            spacing="md",
            children=[_graph(fig_types, "postcode-types-graph"), _graph(fig_tx, "postcode-tx-graph")],
        ),
        dmc.Title("Recent transactions", order=5, c="gray.4"),
        _recent_transactions_table(df),
        dmc.Title("Top appreciation (repeat sales)", order=5, c="gray.4"),
        _appreciation_table(appr),
    ]
