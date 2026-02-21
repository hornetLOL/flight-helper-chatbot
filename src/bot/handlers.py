"""
Обработчики команд и сообщений для flight-helper-chatbot (Этап 3).

Добавлено:
- Интеграция с OpenSky Network API (доступен из РФ)
- Обработка номера рейса → callsign
- Резервная заглушка при недоступности API
- Форматированный вывод данных о рейсе
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from src.api_clients.opensky_client import opensky_client
import logging

logger = logging.getLogger(__name__)
router = Router(name="main_handlers")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "✈️ <b>Flight Helper Chatbot</b>\n\n"
        "Привет! Я помогу узнать информацию о рейсах.\n"
        "\n"
        "📚 Доступные команды:\n"
        "/help — справка по возможностям\n"
        "/about — информация о проекте\n"
        "/flight SU1234 — статус рейса (тестовый режим)\n"
        "\n"
        "⚠️ <i>Учебный проект. Данные из открытых источников.</i>",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Справка</b>\n\n"
        "<b>Текущий этап:</b> 3/6 — интеграция с авиационными данными\n\n"
        "<b>Как проверить рейс:</b>\n"
        "<code>/flight SU1234</code>\n\n"
        "<b>Поддерживаемые авиакомпании (учебно):</b>\n"
        "• SU — Аэрофлот (пример: SU1234)\n"
        "• S7 — S7 Airlines (пример: S7123)\n"
        "• DP — Победа (пример: DP456)\n\n"
        "<b>Важно для РФ:</b>\n"
        "• Данные берутся из открытого источника OpenSky Network\n"
        "• Если рейс не в эфире — покажу заглушку\n"
        "• Точность данных зависит от доступности API",
        parse_mode="HTML"
    )


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(
        "🎓 <b>О проекте</b>\n\n"
        "<b>Цель:</b> Обучение интеграции с внешними API и работе с данными.\n\n"
        "<b>Технологии:</b>\n"
        "• Python 3.14.0\n"
        "• aiogram 3.12\n"
        "• OpenSky Network API (доступен из РФ)\n\n"
        "<b>Статус:</b>\n"
        "Учебный проект. Не связан с авиакомпаниями.\n\n"
        "<b>Исходный код:</b>\n"
        "https://github.com/ваш-логин/flight-helper-chatbot",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(Command("flight"))
async def cmd_flight(message: Message) -> None:
    """
    Обработчик команды /flight с интеграцией OpenSky API.

    Логика для РФ:
    1. Преобразуем номер рейса в callsign
    2. Запрашиваем данные у OpenSky
    3. Если API недоступен — показываем заглушку
    4. Форматируем ответ для пользователя
    """
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "🛫 <b>Статус рейса</b>\n\n"
            "Укажите номер рейса после команды:\n"
            "<code>/flight SU1234</code>\n\n"
            "Поддерживаемые форматы:\n"
            "• SU1234 (Аэрофлот)\n"
            "• S7123 (S7 Airlines)\n"
            "• DP456 (Победа)",
            parse_mode="HTML"
        )
        return

    flight_number = args[0].upper().strip()
    callsign = opensky_client.flight_number_to_callsign(flight_number)

    logger.info(f"Запрос статуса рейса: {flight_number} → callsign: {callsign}")

    # Запрос к OpenSky API
    flight_data = await opensky_client.get_flight_by_callsign(callsign)

    if flight_data:
        # Формируем красивый ответ с данными
        status_emoji = "🛬 На земле" if flight_data["on_ground"] else "✈️ В воздухе"
        altitude_info = (
            f"{flight_data['altitude_m']} м"
            if not flight_data["on_ground"]
            else "На земле"
        )

        response = (
            f"✅ <b>Рейс {flight_number} найден!</b>\n\n"
            f"<b>Callsign:</b> {flight_data['callsign']}\n"
            f"<b>Статус:</b> {status_emoji}\n"
            f"<b>Страна:</b> {flight_data['origin_country']}\n"
            f"<b>Высота:</b> {altitude_info}\n"
            f"<b>Скорость:</b> {flight_data['velocity_kmh']} км/ч\n"
            f"<b>Направление:</b> {flight_data['heading']}°\n\n"
            f"<i>Данные: OpenSky Network (реальное время)</i>"
        )
    else:
        # Резервная заглушка (если рейс не в эфире или API недоступен)
        response = (
            f"⚠️ <b>Рейс {flight_number}</b>\n\n"
            "Не удалось получить данные в реальном времени.\n\n"
            "<b>Возможные причины:</b>\n"
            "• Рейс не в эфире (ещё не вылетел/уже приземлился)\n"
            "• Самолёт не оснащён ADS-B транспондером\n"
            "• Временная недоступность OpenSky API\n\n"
            "<b>Учебная информация:</b>\n"
            "Номер рейса: {flight_number}\n"
            "Callsign (для поиска): {callsign}\n\n"
            "<i>Это учебный проект. Для точной информации обращайтесь к авиакомпании.</i>"
        ).format(flight_number=flight_number, callsign=callsign)

    await message.answer(response, parse_mode="HTML")


@router.message()
async def echo_handler(message: Message) -> None:
    """Эхо-обработчик для текстовых сообщений"""
    if not message.text:
        await message.answer(
            "💬 Я обрабатываю только текст.\n"
            "Попробуйте команды:\n"
            "/help — справка\n"
            "/flight SU1234 — статус рейса"
        )
        return

    await message.answer(f"🔁 <b>Эхо:</b>\n\n{message.text}", parse_mode="HTML")