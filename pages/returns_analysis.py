import dash
from dash import html, dcc, dash_table

from data.data_manager import datamanager
from src.returns_analysis import analyse_returns_characteristics
import pandas as pd
dash.register_page(__name__,path = '/log-return-summary')

returns = datamanager.grab_ohlc_data()
returns_summary, summary_table, sample_fig = analyse_returns_characteristics(returns, False)

summary_df = pd.DataFrame(
        data = [[i[0],round(i[1],5)] for i in returns_summary.items()],
        columns = ["stats", "value"]
    )
layout = html.Div(
    [
        html.H1("Log Returns analysis"),
        html.Div(
            [
                html.H2("Sample Summary"),
                # dcc.Graph(
                #     id = "summary-table",
                #     figure = summary_table
                # )
                dash_table.DataTable(
                    id = "sample-summary-table",
                    data = summary_df.to_dict("records"),
                    columns=[{"name": i, "id": i} for i in summary_df.columns],
                    style_table={
                        'height': '100%',  # Fill parent height
                        'overflowY': 'auto'  # Add scroll if needed
                    },
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontFamily': 'Arial',
                        'fontSize': '12px'
                    },
                    style_header={
                        'backgroundColor': '#2c3e50',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data={
                        'backgroundColor': '#f8f9fa',
                        'color': 'black'
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#ffffff'
                        }
                    ]
                )
                
            ],
            className = "graph-module"
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
            className = "graph-module"
        ),
    ]
)