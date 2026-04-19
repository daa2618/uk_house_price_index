import pandas as pd  # noqa: F401 — re-exported via categories
import plotly.express as px  # noqa: F401 — re-exported
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots  # noqa: F401 — re-exported

pio.templates["myWatermark"] = go.layout.Template(
    layout_annotations=[
        dict(
            name="watermark",
            text="Dev Anbarasu",
            opacity=0.1,
            font=dict(color="white", size=25),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
        )
    ]
)

pio.templates.default = "plotly_dark+myWatermark"
