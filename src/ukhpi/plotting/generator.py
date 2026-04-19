from __future__ import annotations

from pathlib import Path

from ukhpi.plotting.hpi_plots import HousePriceIndexPlots
from ukhpi.plotting.save import PlotSaver

_IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"


def main() -> None:
    hpi_plots = HousePriceIndexPlots(region="united-kingdom")
    plot_funcs = [name for name in dir(hpi_plots) if name.startswith("plot")]

    for name in plot_funcs:
        suffix = f"_{hpi_plots._region}_{hpi_plots._start_year}_{hpi_plots._end_year}"
        file_name = name.replace("plot_", "") + suffix
        print("-" * 100)
        print(file_name)
        try:
            fig = getattr(hpi_plots, name)()
            PlotSaver(
                fig=fig,
                file_name=file_name,
                image_type="png",
                base_path=_IMAGES_DIR,
            ).save()
        except Exception as e:
            print(e)
            continue
    print("-" * 100)


if __name__ == "__main__":
    main()
