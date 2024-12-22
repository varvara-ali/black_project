from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from accuweather import WeatherManager

import asyncio

from config import Config

#  Map для удобного отображения кнопок 
parameters_map = {
    k: v[0]
    for k, v in Config.parameters_map.items()
}
parameters_map['show_graphs'] = 'Получить прогноз'

# Объект бота
bot = Bot(token=Config.bot_token)
dp = Dispatcher(storage=MemoryStorage())


# Класс для сохранения состояния
class Form(StatesGroup):
    first_point = State()
    end_point = State()
    forecast_days = State()
    graph = State()


# In-line клавиатуры
graph_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=k) for k, v in list(parameters_map.items())[:2]],
        [InlineKeyboardButton(text=v, callback_data=k) for k, v in list(parameters_map.items())[2:5]],
        [InlineKeyboardButton(text=v, callback_data=k) for k, v in list(parameters_map.items())[5:]],
    ])


# Команда /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer('''
    Это бот для отображения прогноза погоды на маршруте.
    /weather для получения погоды.
    /help для подробной инструкции.
    ''')


# Команда /start
@dp.message(Command('help'))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer('''
    Как пользоваться этим ботом:
    - Для начала используй команду /weather
    - Затем введи координаты начальной точки маршрута: 2 числа от -90 до 90, разделенные пробелом.
    - Потом координаты конечной точки маршрута: 2 числа от -90 до 90, разделенные пробелом.
    - Выбери количество дней (от 1 до 5), на которые ты хочешь получить прогноз.
    - С помощью in-line кнопок выбери необходимые погодные показатели, которые хочешь узнать
    - Когда выберешь необходимые, нажми кнопку получить прогноз.
    ''')


# Команда /weather
@dp.message(Command('weather'))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer("Введите координату начала маршрута(два числа от -90 до 90 через пробел ): ")
    await state.set_state(Form.first_point)


# Обработка ввода стартовой точки маршрута
@dp.message(Form.first_point)
async def process_first_message(message: types.Message, state: FSMContext):
    try:
        # Проверяем корректность координат и возможность получить погоду в точке
        latitude, longitude = map(float, message.text.split())
        if not (-90 <= latitude <= 90 and -90 <= longitude <= 90):
            raise ValueError()
        weather_manager = WeatherManager()
        location_key = weather_manager.get_location_key(latitude, longitude)

        # Если проверка прошла успешно сохраняем первую точку
        await state.update_data(start_point=(latitude, longitude))

        # Запрашиваем следующую точку
        await message.answer("Введите координату конца маршрута(два числа через пробел): ")
        await state.set_state(Form.end_point)
    except ValueError:
        # В случае некорректно введенных координат первой точки, запрашиваем её ещё раз
        await message.answer("Вы ввели координаты в некорректном формате \n"
                             "Введите координату начала маршрута(два числа от -90 до 90 через пробел ): ")
    except RuntimeError as e:
        await message.answer(f"Произошла ошибка при волучении координат:\n{e}")


# Обработка ввода конечной точки маршрута
@dp.message(Form.end_point)
async def process_second_message(message: types.Message, state: FSMContext):
    try:
        # Проверяем корректность координат и возможность получить погоду в точке
        latitude, longitude = map(float, message.text.split())
        if not (-90 <= latitude <= 90 and -90 <= longitude <= 90):
            raise ValueError()
        weather_manager = WeatherManager()
        location_key = weather_manager.get_location_key(latitude, longitude)

        # Если проверка прошла успешно сохраняем первую точку
        await state.update_data(end_point=(latitude, longitude))

        # Создаем inline-клавиатуру
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 день", callback_data="1"),
             InlineKeyboardButton(text="5 дней", callback_data="5")]
        ])

        # Запрашиваем количество дней для прогноза
        await message.answer("Введите количество дней для предсказания (число от 1 до 5):", reply_markup=keyboard)
        await state.set_state(Form.forecast_days)
    except ValueError:
        # В случае некорректно введенных координат второй точки, запрашиваем её ещё раз
        await message.answer("Вы ввели координаты в некорректном формате \n"
                             "Введите координату конца маршрута(два числа от -90 до 90 через пробел ): ")
    except RuntimeError as e:
        await message.answer(f"Произошла ошибка при волучении координат:\n{e}")

#  Обработка ввода количества дней (если ввели текстом)
@dp.message(Form.forecast_days)
async def process_number(message: types.Message, state: FSMContext):
    await handle_number_message(message.text, message, state)


#  Обработка ввода количества дней (если выбрали кнопкой)
@dp.callback_query(Form.forecast_days)
async def process_number_button(callback: types.CallbackQuery, state: FSMContext):
    await handle_number_message(callback.data, callback.message, state)
    await callback.answer()


# Обработка результатов ввода дней прогноза
async def handle_number_message(number_str, reply_to, state: FSMContext):
    try:
        # Проверяем корректность дней прогноза
        forecast_days = int(number_str)
        if not 1 <= forecast_days <= 5:
            raise ValueError()
    except ValueError:
        # В случае некорректно введенного количества дней, запрашиваем его ещё раз
        await reply_to.answer("Пожалуйста, введите корректное число (от 1 до 5).")
        return

    # Сохраняем дни прогноза
    await state.update_data(forecast_days=forecast_days)

    # Запрашиваем необходимые графики
    await reply_to.answer("График :", reply_markup=graph_keyboard)
    await state.set_state(Form.graph)


@dp.callback_query(Form.graph)
async def show_graph(callback: types.CallbackQuery, state: FSMContext):
    # Получение всех данных из state
    data = await state.get_data()
    start_point = data['start_point']
    end_point = data['end_point']
    forecast_days = data['forecast_days']
    selected_graphs = data.get('graph', [])

    command = callback.data
    if command == 'show_graphs':  # Обработка команды "Получить прогноз"
        if not selected_graphs:  # Если графики не выбраны, то запросим их ещё раз
            await callback.message.delete()
            await callback.message.answer(f"Вы не выбрали не одного графика. \n"
                                          f"Выберете хотя бы один что бы получить прогноз :",
                                          reply_markup=graph_keyboard)

            await state.set_state(Form.graph)
        else:  # Если графики выбраны
            # Помещаем все данные в url
            params = [
                f"start_point={';'.join(map(str, start_point))}",
                f"end_point={';'.join(map(str, end_point))}",
                f"selected_graphs={';'.join(selected_graphs)}",
                f"forecast_days={forecast_days}",
            ]
            encoded_params = '&'.join(params)
            base_url = f'http://{Config.url}:{Config.port}/'
            url_with_params = f"{base_url}?{encoded_params}"

            # Возвращаем ссылку на визуализацию
            await callback.message.answer(url_with_params, parse_mode='HTML')
            # Сбрасываем state
            await state.clear()
    else:  # Обработка добавления/удаления графика
        if command in selected_graphs:
            action = 'удален'
            selected_graphs.remove(command)
        else:
            action = 'добавлен'
            selected_graphs.append(command)
        # Перезапись выбранных графиков
        await state.update_data(graph=selected_graphs)

        # Запрос следующих графиков или получения прогноза
        await callback.message.delete()
        await callback.message.answer(f"График {parameters_map[command]} {action}. \n"
                                      f"Выбраны графики: \n{'\n'.join(map(lambda x: parameters_map[x], selected_graphs))} \n"
                                      f"Выберете следующий или получите прогноз :", reply_markup=graph_keyboard)
        await state.set_state(Form.graph)


if __name__ == '__main__':
    # Асинхронный запуск бота
    async def main():
        await dp.start_polling(bot)

    asyncio.run(main())
