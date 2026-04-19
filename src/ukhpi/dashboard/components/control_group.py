from __future__ import annotations

from dash import html
from dash.development.base_component import Component


def control_group(label: str, control: Component, *, flex: str = "1", min_width: str = "250px") -> html.Div:
    return html.Div(
        className="control-item",
        style={"flex": flex, "minWidth": min_width},
        children=[
            html.Div(
                className="control-group",
                children=[
                    html.Label(label, className="control-label"),
                    control,
                ],
            )
        ],
    )
