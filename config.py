import logging

class Config:
    accuweather_key = 'NRsCPXZ9aYVBjl28TqxjvfWZ1xhA8Occ'
    logging_level = logging.INFO

    url = '127.0.0.1'
    port = 8050

    parameters_map = {
    'min_temperature': ['Минимальная температура', '°C'],
    'max_temperature': ['Максимальная температура', '°C'],
    'mean_temperature': ['Средняя температура', '°C'],
    'relative_humidity': ['Относительная влажность', '%'],
    'precipitation_probability': ['Вероятность осадков', '%'],
    'wind_speed': ['Скорость ветра', 'км/ч'],
}
    bot_token = 'Paste your bot token here'