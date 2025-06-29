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

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x = np.arange(1,101),
            y = var_res,
            mode = "lines",
            line = {
                "color" : "black"
            }
        )
    )
    fig.add_vline(
        x = 5,
        line_dash = "dash",
        line_color = "red",
        label = {
            "text" : "P95 Losses",
            "textposition" : "top left"
        }
    )
    fig.update_layout(
        title_text = f"VaR Curve\nP95 losses ${dollar_format(var_res[4])}"
    )

    if save_path:
        fig.write_html(save_path)
    else:
        fig.show()
