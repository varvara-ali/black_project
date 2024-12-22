import dash
from click import style
from dash import html, dcc, Input, Output, State, callback
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import logging

from config import Config
from accuweather import WeatherManager
import plotly.graph_objs as go

import plotly_graphs

app = dash.Dash(__name__)


parameters_map = Config.parameters_map

div_stile = {
    'margin-top': '20px',
    'border': '2px solid black',  # Толщина и цвет рамки
    'padding': '10px',            # Внутренний отступ
    'border-radius': '5px',       # Закругленные углы
    'width': '300px',             # Ширина рамки
}


app.layout = html.Div([
    # Получение url
    dcc.Location(id='url', refresh=False),
    # Вывод графиков
    html.Div(id='simple_out')
])


# Отображение графиков
@app.callback(
    Output('simple_out', 'children'),
    Input('url', 'search')
)
def update_graphs(search):
    params = dict(
        param.split('=')
        for param in search.strip('?').split('&')
    ) if search else {}
    points = [
        tuple(map(float, params['start_point'].split(';'))),
        tuple(map(float, params['end_point'].split(';')))
    ]
    forecast_days = int(params['forecast_days'])
    selected_graphs = params['selected_graphs'].split(';')
    weather_manager = WeatherManager()
    try:
        location_keys = [
            weather_manager.get_location_key(*point)
            for point in points
        ]
    except RuntimeError as e:
         return html.H2(f"Ошибка при получении ключа локации:\n {e}")

    try:
        weather_data = [
            weather_manager.get_weather(location_key, name='test')
            for location_key in location_keys
        ]
    except RuntimeError as e:
        return html.H2(f"Ошибка при получении погоды:\n {e}")


    graphs = plotly_graphs.make_weather_graph(weather_data, forecast_days, selected_graphs)
    graphs = [dcc.Graph(figure=fig) for fig in graphs]
    return graphs


if __name__ == '__main__':
    app.run_server(debug=True, host=Config.url, port=Config.port)
