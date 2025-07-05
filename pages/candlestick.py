import dash
from dash import html, dcc

from data.data_manager import datamanager
from src.chart_visual import chart_visuals

dash.register_page(__name__,path = '/candlestick')

candle_stick = chart_visuals(datamanager.grab_ohlc_data())

layout = html.Div(
    [
        html.H1("SOLUSDC Candlestick"),
        html.Div(
            [
                dcc.Graph(id = "candle-stick", figure=candle_stick)
            ]
        )
    ],
    className = "graph-module"
)