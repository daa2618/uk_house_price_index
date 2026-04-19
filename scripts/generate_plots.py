from __future__ import annotations

import argparse
from pathlib import Path

from ukhpi.plotting.hpi_plots import HousePriceIndexPlots
from ukhpi.plotting.save import PlotSaver

DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "src" / "ukhpi" / "images"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Regenerate the static HPI plot gallery as PNGs.")
    parser.add_argument("--start-year", type=int, default=2020, help="Earliest HPI year (default: 2020)")
    parser.add_argument("--end-year", type=int, default=2024, help="Latest HPI year (default: 2024)")
    parser.add_argument(
        "--region",
        type=str,
        default="united-kingdom",
        help="Region slug, e.g. 'united-kingdom', 'london' (default: united-kingdom)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory to write PNGs into (default: {DEFAULT_OUTPUT_DIR})",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    hpi_plots = HousePriceIndexPlots(
        start_year=args.start_year,
        end_year=args.end_year,
        region=args.region,
    )
    plot_funcs = [name for name in dir(hpi_plots) if name.startswith("plot")]

    suffix = f"_{hpi_plots._region}_{hpi_plots._start_year}_{hpi_plots._end_year}"
    for name in plot_funcs:
        file_name = name.replace("plot_", "") + suffix
        print("-" * 100)
        print(file_name)
        try:
            fig = getattr(hpi_plots, name)()
            PlotSaver(
                fig=fig,
                file_name=file_name,
                image_type="png",
                base_path=args.output_dir,
            ).save()
        except Exception as e:
            print(e)
            continue
    print("-" * 100)


if __name__ == "__main__":
    main()
