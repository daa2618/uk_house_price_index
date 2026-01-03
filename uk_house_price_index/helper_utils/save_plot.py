import datetime
import os
import pathlib
from typing import Optional, Union

import plotly.graph_objects as go
# kaleido is required by fig.write_image but isn't directly imported in the class.
# It's good practice to ensure it's installed.

class PlotSaver:
    """
    A robust and easy-to-use class for saving Plotly figures.

    This class handles path creation, filename uniqueness, and saving to various
    static image formats or interactive HTML files.

    Args:
        fig (go.Figure): The Plotly figure object to save.
        file_name (str): The base name of the file (without extension).
        image_type (str): The image format (e.g., "png", "pdf", "svg").
                          This is ignored when exporting to HTML.
        base_path (Union[str, pathlib.Path], optional): The directory to save files in.
                                                        Defaults to a "plots" directory.
        recurring (bool, optional): If True, appends a counter to the filename if it
                                    already exists (e.g., 'my_plot_1.png'). If False,
                                    it overwrites any existing file. Defaults to False.
        scale (int, optional): Scaling factor for static images. Defaults to 6.
        width (int, optional): Width of the static image in pixels. Defaults to 600.
        height (int, optional): Height of the static image in pixels. Defaults to 540.

    Raises:
        TypeError: If input arguments have invalid types.
        ValueError: If `image_type` is not a supported format.
        
    Example:
        >>> import plotly.express as px
        >>> df = px.data.iris()
        >>> fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species")
        
        >>> # Save a plot, overwriting if it exists
        >>> saver = PlotSaver(fig, "iris_scatter", "png")
        >>> saved_path = saver.save()
        >>> print(f"Plot saved to: {saved_path}")

        >>> # Save as an interactive HTML file
        >>> html_path = saver.export_to_html()
        >>> print(f"HTML saved to: {html_path}")
    """
    SUPPORTED_IMAGE_TYPES = {"png", "jpeg", "webp", "svg", "pdf", "eps", "html"}

    def __init__(
        self,
        fig: go.Figure,
        file_name: str,
        image_type: str,
        base_path: Union[str, pathlib.Path] = "images",
        recurring: bool = False,
        scale: int = 6,
        width: int = 600,
        height: int = 540,
    ):
        # --- Input Validation (Fail-Fast) ---
        if not isinstance(fig, go.Figure):
            raise TypeError("`fig` must be a plotly.graph_objects.Figure object.")
        if not isinstance(file_name, str) or not file_name:
            raise TypeError("`file_name` must be a non-empty string.")
        if image_type.lower() not in self.SUPPORTED_IMAGE_TYPES:
            raise ValueError(
                f"`image_type` must be one of {self.SUPPORTED_IMAGE_TYPES}. "
                f"Got '{image_type}'."
            )
        for name, val in [("scale", scale), ("width", width), ("height", height)]:
            if not isinstance(val, int):
                raise TypeError(f"`{name}` must be an integer.")

        self.fig = fig
        self.file_name = file_name
        self.image_type = image_type.lower()
        self.base_path = pathlib.Path(base_path)
        self.recurring = recurring
        self.scale = scale
        self.width = width
        self.height = height

    def _get_save_path(self, extension: str) -> pathlib.Path:
        """
        Constructs the final save path, handling directory creation and filename conflicts.
        """
        # Ensure the target directory exists
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Sanitize extension
        clean_extension = extension.lstrip(".").lower()
        
        save_path = self.base_path / f"{self.file_name}.{clean_extension}"

        if self.recurring:
            # Append a counter if the file exists
            counter = 1
            while save_path.exists():
                save_path = self.base_path / f"{self.file_name}_{counter}.{clean_extension}"
                counter += 1
        elif save_path.exists():
            # If not recurring, simply overwrite by deleting the old file first
            # Note: write_image/write_html would overwrite anyway, but this is explicit.
            save_path.unlink()
            
        return save_path

    def save(self) -> pathlib.Path:
        """
        Saves the figure as a static image file (e.g., png, pdf).

        Returns:
            pathlib.Path: The absolute path to the saved image file.
        """
        file_path = self._get_save_path(self.image_type)
        
        self.fig.write_image(
            file_path,
            scale=self.scale,
            width=self.width,
            height=self.height,
            engine="kaleido"
        )
        
        abs_path = file_path.resolve()
        print(f"Figure saved to: {abs_path}")
        return abs_path

    def export_to_html(
        self,
        full_html: bool = True,
        include_plotly_js: str = "cdn"
    ) -> pathlib.Path:
        """
        Exports the figure as an interactive HTML file.

        Args:
            full_html (bool, optional): If True, saves as a full standalone HTML file.
                                        Defaults to True.
            include_plotly_js (str, optional): Can be 'cdn' to load from a CDN (smaller
                                               file) or 'embed' to include the JS in
                                               the file. Defaults to "cdn".

        Returns:
            pathlib.Path: The absolute path to the saved HTML file.
        """
        file_path = self._get_save_path("html")

        self.fig.write_html(
            file_path,
            full_html=full_html,
            include_plotlyjs=include_plotly_js,
            config={'scrollZoom': True, 'responsive': True},
            auto_open=False
        )

        abs_path = file_path.resolve()
        print(f"Figure exported to HTML: {abs_path}")
        return abs_path


if __name__ == '__main__':
    # This block demonstrates how to use the improved class.
    # It will only run when the script is executed directly.
    import plotly.express as px
    import shutil

    # 1. Create a sample figure
    df = px.data.iris()
    fig = px.scatter(
        df, x="sepal_width", y="sepal_length", color="species",
        title="Iris Dataset Scatter Plot"
    )

    print("--- Demo: Basic Save (PNG) ---")
    # This will create a 'plots' directory if it doesn't exist.
    saver = PlotSaver(fig, "iris_plot", "png")
    saved_file = saver.save()
    print(f"Returned path: {saved_file}\n")

    print("--- Demo: Save with Recurring (appends counter) ---")
    # First save
    recurring_saver = PlotSaver(fig, "iris_recurring", "svg", recurring=True)
    recurring_saver.save()
    # Second save - should create 'iris_recurring_1.svg'
    recurring_saver.save()
    # Third save - should create 'iris_recurring_2.svg'
    recurring_saver.save()
    print("")

    print("--- Demo: Export to HTML ---")
    html_path = saver.export_to_html()
    print(f"Returned path: {html_path}\n")

    print("--- Demo: Save to a different directory ---")
    custom_path_saver = PlotSaver(fig, "iris_custom_path", "pdf", base_path="temp_plots/project_a")
    custom_path_saver.save()

    # Clean up the created directories for a clean run next time
    if os.path.exists("plots"):
        shutil.rmtree("plots")
    if os.path.exists("temp_plots"):
        shutil.rmtree("temp_plots")

    print("\n--- Demo Finished ---")