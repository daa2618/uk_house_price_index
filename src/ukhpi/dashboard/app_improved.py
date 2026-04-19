from __future__ import annotations

import webbrowser

import dash

from ukhpi.dashboard.callbacks import register_callbacks
from ukhpi.dashboard.layout import build_layout


def _create_app() -> dash.Dash:
    app = dash.Dash(__name__, suppress_callback_exceptions=True)
    app.title = "UK House Price Index Dashboard"
    app.layout = build_layout()
    register_callbacks(app)
    return app


app = _create_app()
server = app.server


def open_browser(host: str, port: int) -> None:
    webbrowser.open_new(f"http://{host}:{port}/")


def main(host: str = "127.0.0.1", port: int = 8054, debug: bool = True, open_browser_tab: bool = True) -> None:
    if open_browser_tab:
        open_browser(host, port)
    app.run(debug=debug, host=host, port=port)
