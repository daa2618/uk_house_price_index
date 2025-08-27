# UK House Price Index Dashboard

![alt text](<Screenshot 2025-08-27 at 16.09.36.jpg>) ![alt text](<Screenshot 2025-08-27 at 16.09.52.jpg>) ![alt text](<Screenshot 2025-08-27 at 16.09.58.jpg>) ![alt text](<Screenshot 2025-08-27 at 16.10.02.jpg>)

A self-serve dashboard and data toolkit for exploring the UK House Price Index (HPI) by geography and time period.

## Features

- Fetches HPI data from the UK Land Registry API for any region and time range.
- Caches and versions downloaded data files for reproducibility.
- Utilities for loading, processing, and saving data in CSV, JSON, Excel, and other formats.
- Plotting utilities using Plotly for interactive visualizations.
- Modular codebase for easy extension and customization.

## Directory Structure

````
uk_house_price_index/
    hpi.py                  # Main HPI data fetching and processing logic
    utils/
        data_loader.py      # Data loading utilities
        data_writer.py      # Data writing/versioning utilities
        data_version.py     # File versioning and cache management
        helper.py           # Logging and helper functions
        basic_plots.py      # Plotting utilities
        plotly_imports.py   # Plotly setup and color schemes
        response.py         # HTTP response handling
        split_from_camel.py # CamelCase to snake_case conversion
    data/                   # Cached data files
    notebooks/              # Example Jupyter notebooks

## Getting Started

1. **Install dependencies**
   Make sure you have Python 3.8+ and install required packages:
   ```sh
   pip install pandas plotly requests pdfplumber geopandas
````

2. **Fetch HPI Data**  
   Use the [`HousePriceIndex`](uk_house_price_index/hpi.py) class to fetch and process data:

   ```python
   from uk_house_price_index.hpi import HousePriceIndex
   hpi = HousePriceIndex()
   data = hpi.fetch_hpi(start_year=2020, end_year=2024, region="west-northamptonshire")
   selected = hpi.select_values(data)
   df = hpi.make_df(selected)
   ```

3. **Plot Data**  
   Use the [`HousePriceIndexPlots`](uk_house_price_index/hpi.py) class for ready-made visualizations.
   ![Average Price By Build Types London 2020 2024](uk_house_price_index/images/average_price_by_build_types_london_2020_2024.png)
   ![Average Price By Build Types West-Northamptonshire 2020 2024](uk_house_price_index/images/average_price_by_build_types_west-northamptonshire_2020_2024.png)
   ![Average Price By Occupant Types West-Northamptonshire 2020 2024](uk_house_price_index/images/average_price_by_occupant_types_west-northamptonshire_2020_2024.png)
   ![Average Price By Payment Types West-Northamptonshire 2020 2024](uk_house_price_index/images/average_price_by_payment_types_west-northamptonshire_2020_2024.png)
   ![Average Price By Property Types London 2020 2024](uk_house_price_index/images/average_price_by_property_types_london_2020_2024.png)
   ![Average Price By Property Types West-Northamptonshire 2020 2024](uk_house_price_index/images/average_price_by_property_types_west-northamptonshire_2020_2024.png)
   ![House Price Index By Build Type London 2020 2024](uk_house_price_index/images/house_price_index_by_build_type_london_2020_2024.png)
   ![House Price Index By Build Type West-Northamptonshire 2020 2024](uk_house_price_index/images/house_price_index_by_build_type_west-northamptonshire_2020_2024.png)
   ![House Price Index By Occupant Types West-Northamptonshire 2020 2024](uk_house_price_index/images/house_price_index_by_occupant_types_west-northamptonshire_2020_2024.png)
   ![House Price Index By Payment Types West-Northamptonshire 2020 2024](uk_house_price_index/images/house_price_index_by_payment_types_west-northamptonshire_2020_2024.png)
   ![House Price Index By Property Types London 2020 2024](uk_house_price_index/images/house_price_index_by_property_types_london_2020_2024.png)
   ![House Price Index By Property Types West-Northamptonshire 2020 2024](uk_house_price_index/images/house_price_index_by_property_types_west-northamptonshire_2020_2024.png)
   ![Percentage Annual Change By Build Types London 2020 2024](uk_house_price_index/images/percentage_annual_change_by_build_types_london_2020_2024.png)
   ![Percentage Annual Change By Build Types West-Northamptonshire 2020 2024](uk_house_price_index/images/percentage_annual_change_by_build_types_west-northamptonshire_2020_2024.png)
   ![Percentage Annual Change By Occupant Types West-Northamptonshire 2020 2024](uk_house_price_index/images/percentage_annual_change_by_occupant_types_west-northamptonshire_2020_2024.png)
   ![Percentage Annual Change By Payment Types West-Northamptonshire 2020 2024](uk_house_price_index/images/percentage_annual_change_by_payment_types_west-northamptonshire_2020_2024.png)
   ![Percentage Annual Change By Property Types West-Northamptonshire 2020 2024](uk_house_price_index/images/percentage_annual_change_by_property_types_west-northamptonshire_2020_2024.png)
   ![Sales Volume By Build Types West-Northamptonshire 2020 2024](uk_house_price_index/images/sales_volume_by_build_types_west-northamptonshire_2020_2024.png)
   ![Sales Volume By Payment Types West-Northamptonshire 2020 2024](uk_house_price_index/images/sales_volume_by_payment_types_west-northamptonshire_2020_2024.png)

4. **Data Versioning**  
   Data files are automatically versioned and cached in the `data/` directory using [`FileVersion`](uk_house_price_index/utils/data_version.py).

## Notebooks

See [try_hpi.ipynb](uk_house_price_index/try_hpi.ipynb) for example usage.

## License

Apache License 2.0. See [LICENSE](LICENSE) for details.

## Author

[Dev Anbarasu](https://github.com/daa2618)
