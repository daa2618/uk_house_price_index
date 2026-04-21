from __future__ import annotations

import dash_mantine_components as dmc
from dash import dcc, html


def chart_card(view: str, method: str, label: str) -> html.Div:
    return html.Div(
        id={"role": "grid-graph-card", "view": view, "method": method},
        n_clicks=0,
        className="chart-card",
        style={"cursor": "pointer"},
        children=dmc.Card(
            withBorder=True,
            radius="md",
            padding="sm",
            children=[
                dmc.Group(
                    justify="space-between",
                    align="center",
                    mb=4,
                    children=[
                        dmc.Text(label, size="sm", fw=600, c="gray.3"),
                        dmc.Text("⤢", size="lg", c="dimmed"),
                    ],
                ),
                dcc.Loading(
                    type="circle",
                    color="#3498db",
                    children=dcc.Graph(
                        id={"role": "grid-graph", "view": view, "method": method},
                        style={"height": "400px"},
                        config={"displayModeBar": False, "displaylogo": False},
                    ),
                ),
            ],
        ),
    )
