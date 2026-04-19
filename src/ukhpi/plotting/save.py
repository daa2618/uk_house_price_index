import pathlib

import plotly.graph_objects as go


class PlotSaver:
    """Save a Plotly figure as a static image or interactive HTML."""

    SUPPORTED_IMAGE_TYPES = {"png", "jpeg", "webp", "svg", "pdf", "eps", "html"}

    def __init__(
        self,
        fig: go.Figure,
        file_name: str,
        image_type: str,
        base_path: str | pathlib.Path = "images",
        recurring: bool = False,
        scale: int = 6,
        width: int = 600,
        height: int = 540,
    ):
        if not isinstance(fig, go.Figure):
            raise TypeError("`fig` must be a plotly.graph_objects.Figure object.")
        if not isinstance(file_name, str) or not file_name:
            raise TypeError("`file_name` must be a non-empty string.")
        if image_type.lower() not in self.SUPPORTED_IMAGE_TYPES:
            raise ValueError(f"`image_type` must be one of {self.SUPPORTED_IMAGE_TYPES}. Got '{image_type}'.")

        self.fig = fig
        self.file_name = file_name
        self.image_type = image_type.lower()
        self.base_path = pathlib.Path(base_path)
        self.recurring = recurring
        self.scale = scale
        self.width = width
        self.height = height

    def _get_save_path(self, extension: str) -> pathlib.Path:
        self.base_path.mkdir(parents=True, exist_ok=True)
        clean_extension = extension.lstrip(".").lower()
        save_path = self.base_path / f"{self.file_name}.{clean_extension}"

        if self.recurring:
            counter = 1
            while save_path.exists():
                save_path = self.base_path / f"{self.file_name}_{counter}.{clean_extension}"
                counter += 1
        elif save_path.exists():
            save_path.unlink()

        return save_path

    def save(self) -> pathlib.Path:
        file_path = self._get_save_path(self.image_type)
        self.fig.write_image(file_path, scale=self.scale, width=self.width, height=self.height, engine="kaleido")
        return file_path.resolve()

    def export_to_html(self, full_html: bool = True, include_plotly_js: str = "cdn") -> pathlib.Path:
        file_path = self._get_save_path("html")
        self.fig.write_html(
            file_path,
            full_html=full_html,
            include_plotlyjs=include_plotly_js,
            config={"scrollZoom": True, "responsive": True},
            auto_open=False,
        )
        return file_path.resolve()
