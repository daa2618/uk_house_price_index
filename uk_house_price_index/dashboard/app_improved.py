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

# Custom CSS styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1e1e1e 0%, #2d2d30 100%);
            }
            
            .main-container {
                background: linear-gradient(135deg, #1e1e1e 0%, #2d2d30 100%);
                min-height: 100vh;
                padding: 0;
                margin: 0;
            }
            
            .header-section {
                background: linear-gradient(90deg, #2c3e50 0%, #3498db 100%);
                padding: 20px 30px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                border-bottom: 3px solid #3498db;
            }
            
            .controls-section {
                background: rgba(42, 42, 42, 0.95);
                padding: 20px 30px;
                border-bottom: 1px solid #444;
                backdrop-filter: blur(10px);
            }
            
            .content-section {
                padding: 0;
                height: calc(100vh - 200px);
                display: flex;
                flex-direction: column;
            }
            
            .control-group {
                margin-bottom: 15px;
                background: rgba(255, 255, 255, 0.05);
                padding: 15px;
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .control-label {
                font-weight: 600;
                margin-bottom: 8px;
                color: #f0f0f0;
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Enhanced Dropdown Styling */
            .Select-control {
                background-color: #3a3a3a !important;
                border: 1px solid #555 !important;
                border-radius: 6px !important;
                color: #f0f0f0 !important;
                min-height: 40px !important;
            }
            
            .Select-control:hover {
                border-color: #3498db !important;
                box-shadow: 0 0 10px rgba(52, 152, 219, 0.3) !important;
            }
            
            .Select-value-label,
            .Select-placeholder {
                color: #f0f0f0 !important;
                font-weight: 500 !important;
            }
            
            .Select-menu-outer {
                background-color: #3a3a3a !important;
                border: 1px solid #555 !important;
                border-radius: 6px !important;
                box-shadow: 0 8px 30px rgba(0,0,0,0.4) !important;
            }
            
            .Select-option {
                background-color: #3a3a3a !important;
                color: #f0f0f0 !important;
                padding: 12px 15px !important;
            }
            
            .Select-option:hover {
                background-color: #3498db !important;
                color: white !important;
            }
            
            /* Tab Styling */
            .tab {
                background: linear-gradient(145deg, #3a3a3a, #2a2a2a) !important;
                border: 1px solid #555 !important;
                border-radius: 8px 8px 0 0 !important;
                margin-right: 2px !important;
                transition: all 0.3s ease !important;
            }
            
            .tab:hover {
                background: linear-gradient(145deg, #4a4a4a, #3a3a3a) !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3) !important;
            }
            
            .tab--selected {
                background: linear-gradient(145deg, #3498db, #2980b9) !important;
                color: white !important;
                border-bottom: 3px solid #3498db !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 20px rgba(52, 152, 219, 0.4) !important;
            }
            
            /* Range Slider */
            .rc-slider-track {
                background: linear-gradient(90deg, #3498db, #2ecc71) !important;
                height: 6px !important;
            }
            
            .rc-slider-handle {
                background: #3498db !important;
                border: 3px solid #fff !important;
                width: 18px !important;
                height: 18px !important;
                margin-top: -6px !important;
                box-shadow: 0 2px 10px rgba(52, 152, 219, 0.5) !important;
            }
            
            .rc-slider-handle:hover {
                box-shadow: 0 4px 20px rgba(52, 152, 219, 0.7) !important;
            }
            
            /* Graph Container */
            .graph-container {
                flex: 1;
                background: rgba(30, 30, 30, 0.95);
                margin: 0;
                padding: 0;
                border-radius: 0;
                height: 100%;
                display: flex;
                flex-direction: column;
            }
            
            .graph-wrapper {
                flex: 1;
                display: flex;
                flex-direction: column;
            }
            
            /* Loading Spinner */
            ._dash-loading-callback {
                color: #3498db !important;
            }
            
            /* Responsive Design */
            @media (max-width: 768px) {
                .controls-row {
                    flex-direction: column !important;
                }
                
                .control-item {
                    width: 100% !important;
                    margin-bottom: 15px !important;
                }
            }
            
            /* Scrollbar Styling */
            ::-webkit-scrollbar {
                width: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: #1e1e1e;
            }
            
            ::-webkit-scrollbar-thumb {
                background: #3498db;
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: #2980b9;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

DEFAULT_START = 2020
DEFAULT_END = 2024
DEFAULT_REGION = "england"

REGIONS = SparqlQuery().HPI_REGIONS["ref_region_keyword"].unique().tolist()

# --- Mapping for each tab ---
TABS = {
    "📊 Average Prices": {
        "Average Price by Build Types": "plot_average_price_by_build_types",
        "Average Price by Occupant Types": "plot_average_price_by_occupant_types",
        "Average Price by Payment Types": "plot_average_price_by_payment_types",
        "Average Price by Property Types": "plot_average_price_by_property_types",
    },
    "📈 House Price Index": {
        "HPI by Build Types": "plot_house_price_index_by_build_type",
        "HPI by Occupant Types": "plot_house_price_index_by_occupant_types",
        "HPI by Payment Types": "plot_house_price_index_by_payment_types",
        "HPI by Property Types": "plot_house_price_index_by_property_types",
    },
    "📉 Sales Volume": {
        "Sales Volume by Build Types": "plot_sales_volume_by_build_types",
        "Sales Volume by Payment Types": "plot_sales_volume_by_payment_types",
        "Sales Volume by Property Types": "plot_sales_volume_by_property_types",
    },
    "📋 % Annual Change": {
        "Change by Build Types": "plot_percentage_annual_change_by_build_types",
        "Change by Occupant Types": "plot_percentage_annual_change_by_occupant_types",
        "Change by Payment Types": "plot_percentage_annual_change_by_payment_types",
        "Change by Property Types": "plot_percentage_annual_change_by_property_types",
    }
}

REGION_OPTIONS = [{"label": f"🏠 {r.title()}", "value": r} for r in REGIONS]

# --- Enhanced Layout ---
app.layout = html.Div(
    className="main-container",
    children=[
        # Header Section
        html.Div(
            className="header-section",
            children=[
                html.H1(
                    "🏘️ UK House Price Index Dashboard", 
                    style={
                        "textAlign": "center", 
                        "color": "white",
                        "margin": "0",
                        "fontSize": "2.5em",
                        "fontWeight": "700",
                        "textShadow": "2px 2px 4px rgba(0,0,0,0.5)"
                    }
                ),
                html.P(
                    "Interactive visualization of UK housing market trends and statistics",
                    style={
                        "textAlign": "center",
                        "color": "#ecf0f1",
                        "margin": "10px 0 0 0",
                        "fontSize": "1.1em",
                        "fontWeight": "300"
                    }
                )
            ]
        ),

        # Controls Section
        html.Div(
            className="controls-section",
            children=[
                html.Div(
                    style={"display": "flex", "flexWrap": "wrap", "gap": "20px", "alignItems": "flex-end"},
                    className="controls-row",
                    children=[
                        # Region Control
                        html.Div(
                            className="control-item",
                            style={"flex": "1", "minWidth": "250px"},
                            children=[
                                html.Div(
                                    className="control-group",
                                    children=[
                                        html.Label("Select Region", className="control-label"),
                                        dcc.Dropdown(
                                            id="region-dropdown",
                                            options=REGION_OPTIONS,
                                            value=DEFAULT_REGION,
                                            clearable=False,
                                            searchable=True,
                                            style={"minWidth": "200px"}
                                        ),
                                    ]
                                )
                            ]
                        ),

                        # Year Range Control
                        html.Div(
                            className="control-item",
                            style={"flex": "2", "minWidth": "300px"},
                            children=[
                                html.Div(
                                    className="control-group",
                                    children=[
                                        html.Label("Year Range", className="control-label"),
                                        dcc.RangeSlider(
                                            id="year-slider",
                                            min=1995, max=2025, step=1,
                                            value=[DEFAULT_START, DEFAULT_END],
                                            marks={y: {"label": str(y), "style": {"color": "#f0f0f0", "fontSize": "12px"}} 
                                                  for y in range(1995, 2026, 5)},
                                            tooltip={"placement": "bottom", "always_visible": True},
                                            allowCross=False
                                        ),
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        ),

        # Tabs Section
        html.Div(
            style={"padding": "0 30px", "background": "rgba(42, 42, 42, 0.95)"},
            children=[
                dcc.Tabs(
                    id="tabs",
                    value="📊 Average Prices",
                    children=[dcc.Tab(label=tab, value=tab, className="tab") for tab in TABS.keys()],
                    style={"marginBottom": "0"}
                )
            ]
        ),

        # Content Section
        html.Div(
            id="tab-content", 
            className="content-section"
        )
    ]
)

# --- Tab content callback ---
@app.callback(
    Output("tab-content", "children"),
    Input("tabs", "value")
)
def render_tab(tab_name):
    return html.Div(
        className="graph-container",
        children=[
            # Plot Selection
            html.Div(
                style={
                    "padding": "20px 30px",
                    "background": "rgba(52, 73, 94, 0.9)",
                    "borderBottom": "2px solid #3498db"
                },
                children=[
                    html.Div(
                        style={"display": "flex", "alignItems": "center", "gap": "15px"},
                        children=[
                            html.Label(
                                "📊 Select Visualization:", 
                                style={
                                    "color": "#ecf0f1", 
                                    "fontWeight": "600",
                                    "fontSize": "16px",
                                    "margin": "0"
                                }
                            ),
                            dcc.Dropdown(
                                id=f"plot-dropdown-{tab_name}",
                                options=[{"label": f"📈 {k}", "value": k} for k in TABS[tab_name].keys()],
                                value=list(TABS[tab_name].keys())[0],
                                style={"minWidth": "300px", "flex": "1"},
                                clearable=False
                            )
                        ]
                    )
                ]
            ),
            
            # Graph Section
            html.Div(
                className="graph-wrapper",
                children=[
                    dcc.Loading(
                        id=f"loading-{tab_name}",
                        type="circle",
                        color="#3498db",
                        children=[
                            dcc.Graph(
                                id=f"graph-{tab_name}",
                                style={"height": "100%", "width": "100%"},
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                                    'toImageButtonOptions': {
                                        'format': 'png',
                                        'filename': f'uk_housing_{tab_name.lower().replace(" ", "_")}',
                                        'height': 800,
                                        'width': 1200,
                                        'scale': 2
                                    }
                                }
                            )
                        ]
                    )
                ]
            )
        ]
    )

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
        
        # Get the figure and enhance it for full-page display
        fig = plot_func()
        
        # Enhance the figure for better full-page display
        fig.update_layout(
            height=None,  # Let it fill the container
            margin=dict(l=50, r=50, t=80, b=50),
            plot_bgcolor='rgba(30, 30, 30, 0.9)',
            paper_bgcolor='rgba(30, 30, 30, 0.9)',
            font=dict(color='#f0f0f0', size=12),
            title=dict(
                font=dict(size=24, color='#ecf0f1'),
                x=0.5,
                y=0.95
            ),
            xaxis=dict(
                gridcolor='rgba(128, 128, 128, 0.3)',
                zerolinecolor='rgba(128, 128, 128, 0.5)'
            ),
            yaxis=dict(
                gridcolor='rgba(128, 128, 128, 0.3)',
                zerolinecolor='rgba(128, 128, 128, 0.5)'
            ),
            legend=dict(
                bgcolor='rgba(42, 42, 42, 0.8)',
                bordercolor='rgba(128, 128, 128, 0.5)',
                borderwidth=1
            )
        )
        
        return fig

def open_browser(port):
    """Open browser after a short delay."""
    webbrowser.open_new(f"http://127.0.0.1:{port}/")

if __name__ == "__main__":
    PORT = 8054
    open_browser(PORT)
    
    # Run the app
    app.run(
        debug=True,
        host="127.0.0.1",
        port=PORT
    )
    