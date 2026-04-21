from __future__ import annotations

import argparse

from ukhpi.dashboard.app import main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Launch the UK HPI Dash dashboard.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8054, help="Port to bind (default: 8054).")
    parser.add_argument("--no-debug", action="store_true", help="Disable Dash debug mode.")
    parser.add_argument("--no-open-browser", action="store_true", help="Do not auto-open a browser tab.")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(
        host=args.host,
        port=args.port,
        debug=not args.no_debug,
        open_browser_tab=not args.no_open_browser,
    )
