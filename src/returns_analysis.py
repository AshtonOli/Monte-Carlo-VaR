from typing import Optional, Tuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from statsmodels.graphics.gofplots import qqplot
from statsmodels.tsa.stattools import acf
import matplotlib.pyplot as plt

def analyse_returns_characteristics(
    returns: pd.DataFrame, save_path: str | bool | None = None
) -> Tuple[dict,go.Figure,go.Figure]:
    returns_summary = {
        "mean": returns.log_returns.mean(),
        "std": returns.log_returns.std(),
        "Sharpe Ratio": returns.log_returns.mean() / returns.log_returns.std(),
        "skewness": stats.skew(returns.log_returns),
        "kurtosis": stats.kurtosis(returns.log_returns),
        "jb_pvalue": stats.jarque_bera(returns.log_returns)[1],
        "min": returns.log_returns.min(),
        "max": returns.log_returns.max(),
    }

    summary_df = pd.DataFrame(
        data = [[i[0],round(i[1],5)] for i in returns_summary.items()]
    )

    summary_table = go.Figure().add_trace(
        go.Table(
            cells = dict(
                values = summary_df.transpose().values.tolist()
            )
        )
    )

    fig = make_subplots(
        rows=2, cols=2, subplot_titles=("Log returns", "Frequency", "Q-Q Plot", "ACF")
    )

    # Log returns plot
    # X -
    # - -

    c_returns = returns.copy()
    log_rolling = c_returns.log_returns.rolling(20)
    c_returns["log_mean"] = log_rolling.mean()
    c_returns["log_std"] = log_rolling.std()

    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=3 * c_returns.log_std,
            mode="lines",
            line={"color": "rgba(255, 0, 0, 0.1)"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=c_returns.log_mean - 3 * c_returns.log_std,
            mode="lines",
            line={"color": "rgba(255, 0, 0, 0.1)"},
            fill="tonexty",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=2 * c_returns.log_std,
            mode="lines",
            line={"color": "rgba(255, 183, 0, 0.1)"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=c_returns.log_mean - 2 * c_returns.log_std,
            mode="lines",
            line={"color": "rgba(255, 183, 0, 0.1)"},
            fill="tonexty",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=c_returns.log_std,
            mode="lines",
            line={"color": "rgba(236, 255, 0, 0.1)"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=c_returns.log_mean - c_returns.log_std,
            mode="lines",
            line={"color": "rgba(236, 255, 0, 0.1)"},
            fill="tonexty",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=returns.closetime,
            y=returns.log_returns,
            name="Log returns",
            mode="lines",
            line={"color": "rgba(0, 135, 255, 0.63)"},
            
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=c_returns.closetime,
            y=c_returns["log_mean"],
            mode="lines",
            line={"color": "black", "dash": "dash"},
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Returns histogram
    # - X
    # - -
    x_range = np.linspace(returns_summary["min"], returns_summary["max"],100)
    normal_dist = stats.norm.pdf(x_range,returns_summary["mean"],returns_summary["std"])
    fig.add_trace(
        go.Histogram(
            x=returns.log_returns,
            name="Log return Frequency",
            marker_color="rgba(0, 135, 255, 0.63)",
            histnorm="probability density",
        ),
        row=1,
        col=2,
    )   
    fig.add_trace(
        go.Scatter(
            x=x_range,
            y=normal_dist,
            mode='lines',
            name='Normal Distribution',
            line=dict(color='red', width=2),
        ),
        row=1,
        col=2,
    )
    fig.add_vline(
        x = returns_summary["mean"],
        line_dash = "dash",
        line_color = "red",
        label = {
            "text" : "Mean",
            "textposition" : "top right"
        },
        row=1,
        col=2,
    )

    # Q-Q Plot
    # - -
    # X -
    qqplot_data = qqplot(returns.log_returns, line="s").gca().lines
    plt.close()
    fig.add_trace(
        go.Scatter(
            x=qqplot_data[0].get_xdata(),
            y=qqplot_data[0].get_ydata(),
            mode="markers",
            marker={"color": "#19d3f3"},
            name="Returns Q-Q",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=qqplot_data[1].get_xdata(),
            y=qqplot_data[1].get_ydata(),
            mode="lines",
            line={"color": "#636efa"},
            name="Normal",
        ),
        row=2,
        col=1,
    )

    # ACF
    # - -
    # - X
    lags = np.arange(1, min(50, len(returns.log_returns) // 4))
    acf_returns = acf(returns.log_returns, nlags=max(lags))[1:]
    acf_squared = acf(returns.log_returns**2, nlags=max(lags))[1:]
    fig.add_trace(
        go.Scatter(x=lags, y=acf_returns[: len(lags)], name="Returns ACF"), row=2, col=2
    )
    fig.add_trace(
        go.Scatter(x=lags, y=acf_squared[: len(lags)], name="Squared Returns ACF"),
        row=2,
        col=2,
    )

    if isinstance(save_path,str):
        fig.write_html(save_path)
    elif save_path is None:
        fig.show()


    return (returns_summary,summary_table,fig)
