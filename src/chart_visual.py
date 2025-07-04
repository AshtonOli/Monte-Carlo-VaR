import plotly.graph_objects as go
import pandas as pd

def chart_visuals(ohlc: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x = ohlc.opentime,
            open = ohlc.open,
            high = ohlc.high,
            low = ohlc.low,
            close = ohlc.close
        )
    )

    # fig.add_trace(
    #     go.Scatter(
    #         x = ohlc.closetime,
    #         y = ohlc.log_returns,
    #         yaxis = "y2"
    #     )
    # )

    return fig