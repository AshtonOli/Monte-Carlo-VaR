import dash
from dash import html, dcc, Input, Output, callback
import plotly.graph_objects as go
from data.data_manager import datamanager
from src.var import produce_var_results


dash.register_page(__name__,path = '/price-paths-risk')

process, comparison_table = datamanager.grab_price_path(False,10,10)
returns = datamanager.grab_ohlc_data()
comparison_table = go.Figure(
    go.Table(
        cells = dict(
            values = comparison_table.reset_index(drop = False).transpose().values.tolist()
        ),
        header = dict(
            values = comparison_table.columns
        )
    )
)
layout = html.Div(
    [
        html.H2("Price paths & Risk"),
        # PROCESS ANALYSIS
        html.Div(
            [
                # PROCESS SELECTION DROPDOWN
                html.Div(
                    [
                        html.H3("Select a process"),
                        dcc.Dropdown(
                            id = "process-select-dd",
                            options = [{"label" : "GBM", "value" : "GBM"},{"label" : "JDP", "value" : "JDP"},{"label" : "OU", "value" : "OU"}],
                            value = "GBM"
                        )
                    ],
                    style = {
                        "flex" : '1',
                        "padding" : "20px",
                        'backgroundColor': '#f8f9fa',
                        'border': '1px solid #dee2e6',
                        'margin': '5px'
                    }
                ),
                # ANALYSIS CHARTS
                html.Div(
                    [
                        html.H3("Analysis"),
                        dcc.Graph(id = "price-path-analysis")
                    ],
                    style = {
                        "flex" : '3',
                        "padding" : "20px",
                        'backgroundColor': '#f8f9fa',
                        'border': '1px solid #dee2e6',
                        'margin': '5px'
                    }
                ),
                # PROCESS COMPARISON
                html.Div(
                    [
                        html.H3("Process Comparison"),
                        dcc.Graph(
                            id = "comparison-table",
                            figure=comparison_table
                        )
                    ],
                    style = {
                        "flex" : '1',
                        "padding" : "20px",
                        'backgroundColor': '#f8f9fa',
                        'border': '1px solid #dee2e6',
                        'margin': '5px'
                    }
                )
            ],
            style={
                'display': 'flex',
                'flex-direction': 'row',
                'gap': '10px',
                'margin': '20px 0',
                'height': '600px'
            }
        )
    ]
)

@callback(
    Output("price-path-analysis","figure"),
    Input("process-select-dd","value")
)
def update_ppa(process_selected : str) -> go.Figure:
    ppa = process.str_select(process_selected)
    fig = produce_var_results(ppa,returns,False)
    return fig