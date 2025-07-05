import dash
from dash import html, dcc

from data.data_manager import datamanager
from src.returns_analysis import analyse_returns_characteristics

dash.register_page(__name__,path = '/log-return-summary')

returns = datamanager.grab_ohlc_data()
_, summary_table, sample_fig = analyse_returns_characteristics(returns, False)

layout = html.Div(
    [
        html.H1("Log Returns analysis"),
        html.Div(
            [
                html.H2("Sample Summary"),
                dcc.Graph(
                    id = "summary-table",
                    figure = summary_table
                )
            ],
            style = {
                "padding" : "20px",
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6',
                'margin': '5px'
            }
        ),
        # ANALYSIS CHARTS
        html.Div(
            [
                html.H2("Sample Analysis"),
                dcc.Graph(
                    id = "sample-analysis",
                    figure = sample_fig
                )
            ],
            style = {
                "padding" : "20px",
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6',
                'margin': '5px'
            }
        ),
    ]
)