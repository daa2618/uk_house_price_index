from __future__ import annotations

import dash_mantine_components as dmc
from dash import html


def build_sidebar(view_config: dict, active_view: str) -> html.Div:
    links = [
        dmc.NavLink(
            id={"role": "view-nav", "view": slug},
            label=cfg["label"],
            active=(slug == active_view),
            variant="filled",
            color="blue",
            style={"borderRadius": "6px", "marginBottom": "4px"},
        )
        for slug, cfg in view_config.items()
    ]
    return html.Div(className="sidebar", children=dmc.Stack(gap=0, children=links))
