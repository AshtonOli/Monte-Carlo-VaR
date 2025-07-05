import dash
from dash import Dash, html, dcc

from data.data_manager import datamanager
from src.util import dollar_format

app = Dash(__name__, use_pages=True)

df = datamanager.grab_ohlc_data()
app.layout = html.Div([
    html.H1('Multi-page SOLUSDC Analysis'),
    html.H3(
            f"Last loaded price: {df.closetime.iloc[-1].strftime('%d-%b-%Y %H:%M:%S')} {dollar_format(df.close.iloc[-1])} SOL/USDC",
            style = {"color":'#2c3e50'}
        ),
    html.Div([
        html.Div(
            dcc.Link(f"{page['name']} - {page['path']}", href=page["relative_path"])
        ) for page in dash.page_registry.values()
    ]),
    dash.page_container
])

if __name__ == '__main__':
    app.run(debug=True, port = 8080)