if __name__ == "__main__":

    from hpi import HousePriceIndexPlots
    from pathlib import Path
    import sys
    pardir = Path(__file__).resolve().parent.parent
    if str(pardir) not in sys.path:
        sys.path.insert(0, str(pardir))
    from utils.save_plot import PlotSaver
    hpi_plots = HousePriceIndexPlots(region="united-kingdom")

    plot_funcs = [func for func in dir(hpi_plots) if func.startswith("plot")]
    for func in plot_funcs:
        print("-"*100)
        func_name = func.replace("plot_", "") + f"_{hpi_plots._region}_{hpi_plots._start_year}_{hpi_plots._end_year}"
        print(func_name)
        try:
            fig = getattr(hpi_plots, func)()
            PlotSaver(fig = fig, 
                    file_name=func_name,
                    image_type="png",
                    base_path=Path(__file__).parent/"images",
                    ).save()
        except Exception as e:
            print(e)
            continue
    print("-"*100)



