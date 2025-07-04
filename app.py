import dash
from dash import dcc, html, Input, Output, callback

from src.returns_analysis import analyse_returns_characteristics
from src.var import produce_var_results

from src.processes import Processes
from src.get_data import HistoricalData
from src.util import parse_json, dollar_format
from src.chart_visual import chart_visuals
import plotly.graph_objects as go
import pandas as pd

import asyncio
import datetime as dt

#######################
# LOAD DATA
# config = parse_json("config.json")

# histdata = HistoricalData(config["binance"]["API_KEY"], config["binance"]["API_SECRET"])
# df = histdata.getKline("SOLUSDC","12h").dropna()

df = pd.read_csv("test_data.csv").dropna()
df["opentime"] = pd.to_datetime(df.opentime)
df["closetime"] = pd.to_datetime(df.closetime)
#######################

#######################
# ANALYSIS
simulate_to = df.closetime.iloc[-1] + dt.timedelta(hours = 5)
given_interval = ( df.closetime.iloc[1] - df.closetime.iloc[0] ).total_seconds()
periods = int((simulate_to - df.closetime.iloc[-1]).total_seconds() / given_interval)
sample_stats, summary_table, sample_fig = analyse_returns_characteristics(df, False)
process = Processes(df,1234)
process_comparison_df = asyncio.run(process.compare_processes(periods,1000))
#######################

#######################
# PROCESS COMPARION PLOTLY TABLE
comparison_table = go.Figure(
    go.Table(
        cells = dict(
            values = process_comparison_df.reset_index(drop = False).transpose().values.tolist()
        ),
        header = dict(
            values = process_comparison_df.columns
        )
    )
)
#######################

#######################
# GENERATE CANDLESTICK PLOT
candlestick_graph = chart_visuals(df)
#######################

#######################
# INSTANIATE APP
app = dash.Dash(__name__)
#######################

#######################
# APP LAYOUT
app.layout = html.Div(
    [
        html.H1(
            "SOLUSDC Analysis",
            style={'text-align': 'center', 'color': '#2c3e50'}
        ),
        html.H3(
            f"Last loaded price: {df.closetime.iloc[-1].strftime('%d-%b-%Y %H:%M:%S')} {dollar_format(df.close.iloc[-1])} SOL/USDC",
            style = {"color":'#2c3e50'}
        ),
        # CANDLESTICK CHART
        html.Div(
            [
                dcc.Graph(
                    id = "candlestick-graph",
                    figure = candlestick_graph
                    )
            ],
            style = {
                "padding" : "20px",
                'backgroundColor': '#f8f9fa',
                'border': '1px solid #dee2e6',
                'margin': '5px'
            }
        ),
        # SUMMARY TABLE
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
#######################

#######################
# UPDATE FOR PRICE PATH ANALYSIS
@callback(
    Output("price-path-analysis","figure"),
    Input("process-select-dd","value")
)
def update_ppa(process_selected : str) -> go.Figure:
    ppa = process.str_select(process_selected)
    fig = produce_var_results(ppa,df,False)
    return fig


if __name__ == "__main__":
    app.run(debug = True, port = 8080)