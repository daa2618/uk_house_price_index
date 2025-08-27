from helper_tools.utils.sys_path_insert import add_to_syspath #type:ignore
from pathlib import Path
add_to_syspath(Path(__file__).resolve().parent.parent)
from sparql import SparqlQuery
import dash
from dash import dcc, html, Input, Output
from hpi import HousePriceIndexPlots
import webbrowser

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

DEFAULT_START = 2020
DEFAULT_END = 2024
DEFAULT_REGION = "england"

REGIONS = SparqlQuery().HPI_REGIONS["ref_region_keyword"].unique().tolist()

# --- Mapping for each tab ---
TABS = {
    "Average Prices": {
        "Average Price by Build Types": "plot_average_price_by_build_types",
        "Average Price by Occupant Types": "plot_average_price_by_occupant_types",
        "Average Price by Payment Types": "plot_average_price_by_payment_types",
        "Average Price by Property Types": "plot_average_price_by_property_types",
    },
    "House Price Index": {
        "HPI by Build Types": "plot_house_price_index_by_build_type",
        "HPI by Occupant Types": "plot_house_price_index_by_occupant_types",
        "HPI by Payment Types": "plot_house_price_index_by_payment_types",
        "HPI by Property Types": "plot_house_price_index_by_property_types",
    },
    "Sales Volume": {
        "Sales Volume by Build Types": "plot_sales_volume_by_build_types",
        "Sales Volume by Payment Types": "plot_sales_volume_by_payment_types",
        "Sales Volume by Property Types": "plot_sales_volume_by_property_types",
        
    },
    "% Annual Change": {
        "Change by Build Types": "plot_percentage_annual_change_by_build_types",
        "Change by Occupant Types": "plot_percentage_annual_change_by_occupant_types",
        "Change by Payment Types": "plot_percentage_annual_change_by_payment_types",
        "Change by Property Types": "plot_percentage_annual_change_by_property_types",
    }
}

REGION_OPTIONS=[{"label": r.title(), "value": r} for r in REGIONS]

# --- Layout ---
app.layout = html.Div(
    style={
        "backgroundColor": "#111111",   # dark dashboard background
        "color": "#f0f0f0",             # default font color
        "minHeight": "100vh",
        "padding": "20px"
    },
    children=[
        html.H1("UK House Price Index Dashboard", 
                style={"textAlign": "center", "color": "#f0f0f0"}),

        html.Div([
            html.Label("Select Region:", style={"fontWeight": "bold", "color": "#f0f0f0"}),
            dcc.Dropdown(
                        id="region-dropdown",
                        options=REGION_OPTIONS,
                        value=DEFAULT_REGION,
                        className="dark-dropdown"   # 🔑 custom class
                    ),
        ], style={"width": "25%", "display": "inline-block"}),

        html.Div([
            html.Label("Year Range:", style={"fontWeight": "bold", "color": "#f0f0f0"}),
            dcc.RangeSlider(
                id="year-slider",
                min=1995, max=2025, step=1,
                value=[DEFAULT_START, DEFAULT_END],
                marks={y: str(y) for y in range(1995, 2026, 5)},
                tooltip={"placement": "bottom", "always_visible": False}
            ),
        ], style={"marginTop": "20px"}),

        dcc.Tabs(
            id="tabs",
            value="Average Prices",
            children=[dcc.Tab(label=tab, value=tab) for tab in TABS.keys()],
            style={"backgroundColor": "#222222", "color": "#f0f0f0"},
            colors={
                "border": "#444",
                "primary": "#444",  # active tab border
                "background": "#222222"
            }
        ),

        html.Div(id="tab-content", style={"marginTop": "20px"})
    ]
)



# --- Tab content callback ---
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab(tab_name):
    return html.Div([
        html.Label("Select Plot:"),
        dcc.Dropdown(
            id=f"plot-dropdown-{tab_name}",
            options=[{"label": k, "value": k} for k in TABS[tab_name].keys()],
            value=list(TABS[tab_name].keys())[0]
        ),
        dcc.Loading(
            dcc.Graph(id=f"graph-{tab_name}"),
            type="circle"
        )
    ])

# --- Figure callbacks, one per tab ---
for tab_name, mapping in TABS.items():
    @app.callback(
        Output(f"graph-{tab_name}", "figure"),
        Input("region-dropdown", "value"),
        Input(f"plot-dropdown-{tab_name}", "value"),
        Input("year-slider", "value"),
        prevent_initial_call="initial_duplicate"
    )
    def update_graph(region, plot_choice, year_range, mapping=mapping):
        start, end = year_range
        hpi_plots = HousePriceIndexPlots(start_year=start, end_year=end, region=region)
        method_name = mapping[plot_choice]
        plot_func = getattr(hpi_plots, method_name)
        return plot_func()

def open_browser(port):
    """Open browser after a short delay."""
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

if __name__ == "__main__":
    PORT = 8054
    open_browser(PORT)
    # Optional: Automatically open browser
    #Timer(1, open_browser).start()
    
    # Run the app
    app.run(
        debug=True,
        host="127.0.0.1",
        port=PORT
    )

