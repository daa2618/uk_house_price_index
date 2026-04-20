from __future__ import annotations

import pandas as pd

HISTORICAL_EVENTS = [
    {"date": "2008-09-15", "label": "GFC (Lehman)", "color": "#e74c3c"},
    {"date": "2016-06-23", "label": "Brexit vote", "color": "#f39c12"},
    {"date": "2020-03-23", "label": "COVID lockdown", "color": "#9b59b6"},
    {"date": "2022-09-23", "label": "Mini-budget", "color": "#3498db"},
]


def _is_time_series(fig) -> bool:
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


def apply_historical_events(fig, enabled: bool = True):
    """Overlay dated vertical markers for major UK-housing-market events."""
    if not enabled or not fig.data or not _is_time_series(fig):
        return fig

    for event in HISTORICAL_EVENTS:
        x_val = pd.to_datetime(event["date"])
        fig.add_shape(
            type="line",
            xref="x",
            yref="paper",
            x0=x_val,
            x1=x_val,
            y0=0,
            y1=1,
            line=dict(color=event["color"], width=1, dash="dot"),
        )
        fig.add_annotation(
            x=x_val,
            y=1,
            xref="x",
            yref="paper",
            text=event["label"],
            showarrow=False,
            textangle=-90,
            xanchor="left",
            yanchor="top",
            font=dict(size=10, color=event["color"]),
        )
    return fig
