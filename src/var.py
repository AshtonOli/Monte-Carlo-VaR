import pandas as pd
import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from typing import Optional
from src.util import dollar_format
def component_var():
    pass

def produce_var_results(price_paths: pd.DataFrame, returns: pd.DataFrame,save_path: Optional[str] = None):
    
    final_values = price_paths.iloc[-1].values
    losses = sorted(returns.close.iloc[-1] - final_values)
    var_res = [np.percentile(losses,i) for i in range(1,101)]

    max_price_col = np.argmax(final_values == max(final_values))
    min_price_col = np.argmax(final_values == min(final_values))

    max_price_path = price_paths[f"sim_{1 + max_price_col}"]
    min_price_path = price_paths[f"sim_{1 + min_price_col}"]

    fig = make_subplots(rows = 1, cols = 2, subplot_titles=("Sample of price paths", "VaR Curve"))

    fig.add_trace(
        go.Scatter(
            x = price_paths.index,
            y = max_price_path,
            name = "Max price path"
        ),
        row = 1,
        col = 1
    )
    
    fig.add_trace(
        go.Scatter(
            x = price_paths.index,
            y = min_price_path,
            name = "Min price path"
        ),
        row = 1,
        col = 1
    )

    for i in (1 + (np.random.random(3)*(len(price_paths.columns)))):
        fig.add_trace(
            go.Scatter(
                x = price_paths.index,
                y = price_paths[f"sim_{int(i)}"],
                showlegend=False
            ),
            row = 1,
            col = 1
        )

    fig.add_trace(
        go.Scatter(
            x = np.arange(1,101),
            y = var_res,
            mode = "lines",
            line = {
                "color" : "black"
            },
            name = "VaR Curve"
        ),
        row = 1,
        col = 2,
    )
    fig.add_vline(
        x = 5,
        line_dash = "dash",
        line_color = "red",
        label = {
            "text" : "P95 Losses",
            "textposition" : "top right"
        },
        row = 1,
        col = 2,
    )
    fig.update_layout(
        title_text = f"VaR Curve:<br>P95 losses {dollar_format(var_res[4])}"
    )

    if save_path:
        fig.write_html(save_path)
    else:
        fig.show()
