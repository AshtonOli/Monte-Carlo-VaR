import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from typing import Optional
from src.util import dollar_format
from scipy import stats


def component_var():
    pass


def produce_var_results(
    price_paths: pd.DataFrame, returns: pd.DataFrame, save_path: Optional[str] = None
):
    final_values = price_paths.iloc[-1].values
    losses = sorted(returns.close.iloc[-1] - final_values)
    var_res = [np.percentile(losses, i) for i in range(1, 101)]

    max_price_col = np.argmax(final_values == max(final_values))
    min_price_col = np.argmax(final_values == min(final_values))

    max_price_path = price_paths[f"sim_{1 + max_price_col}"]
    min_price_path = price_paths[f"sim_{1 + min_price_col}"]

    fig = make_subplots(
        rows=2,
        cols=3,
        subplot_titles=("Sample of price paths", "VaR Curve"),
        specs=[
            [{},{},{}],
            [{"type" : "table","colspan" : 3}, None, None]
        ],
    )

    # Simulated price paths
    # X - -
    # - - -
    fig.add_trace(
        go.Scatter(x=price_paths.index, y=max_price_path, name="Max price path"),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(x=price_paths.index, y=min_price_path, name="Min price path"),
        row=1,
        col=1,
    )

    for i in 1 + (np.random.random(3) * (len(price_paths.columns))):
        fig.add_trace(
            go.Scatter(
                x=price_paths.index, y=price_paths[f"sim_{int(i)}"], showlegend=False
            ),
            row=1,
            col=1,
        )

    fig.update_yaxes(tickformat="$,.2f", title_text="Price", row=1, col=1)
    fig.update_xaxes(title_text="Time", row=1, col=1)

    # VaR Curve
    # - X -
    # - - -
    fig.add_trace(
        go.Scatter(
            x=np.arange(1, 101),
            y=var_res,
            mode="lines",
            line={"color": "black"},
            name="VaR Curve",
        ),
        row=1,
        col=2,
    )
    fig.add_vline(
        x=5,
        line_dash="dash",
        line_color="red",
        label={"text": "P95 Losses", "textposition": "top right"},
        row=1,
        col=2,
    )
    fig.update_yaxes(
        tickformat="$,.2f",
        title_text="Losses",
        row=1,
        col=2,
    )
    fig.update_xaxes(
        title_text="Percentile",
        row=1,
        col=2,
    )

    # Final Prices distribution
    # - - X
    # - - -
    final_prices = price_paths.iloc[-1]
    x_range = np.linspace(final_prices.min(), final_prices.max(), 100)
    normal_dist = stats.norm.pdf(x_range, final_prices.mean(), final_prices.std())

    fig.add_trace(
        go.Histogram(
            x=final_prices,
            name="Final Prices",
            marker_color="rgba(0, 135, 255, 0.63)",
            histnorm="probability density",
        ),
        row=1,
        col=3,
    )
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=normal_dist,
            mode="lines",
            line=dict(color="red"),
            name="",
            showlegend=False,
        ),
        row=1,
        col=3,
    )
    fig.add_vline(
        x=returns.close.iloc[-1],
        line_dash="dash",
        line_color="black",
        label={"text": "Current Price", "textposition": "top right"},
        row=1,
        col=3,
    )

    fig.update_xaxes(
        title_text="Final Prices",
        tickformat="$,.2f",
        row=1,
        col=3,
    )

    # Table:
    # - - -
    # X - -
    fig.add_trace(
        go.Table(
            cells = dict(
                values = [
                    ["Max price change", "Min price change", "Average price change", "P95 Loss"],
                    [dollar_format(max(final_values)),dollar_format(min(final_values)), dollar_format(np.mean(final_values)),dollar_format(var_res[4])]
                ]
            )
        ),
        row = 2,
        col = 1
    )

    if save_path:
        fig.write_html(save_path)
    else:
        fig.show()
