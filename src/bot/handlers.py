"""
Обработчики команд и сообщений для flight-helper-chatbot (Этап 4).

Добавлено:
- Интент-классификация через регулярные выражения
- Понимание свободного текста без команд
- Единая точка обработки всех сообщений
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from src.api_clients.opensky_client import opensky_client
from src.api_clients.ai_client import ai_client
from src.core.intent_service import intent_service, Intent
from src.core.config import settings
from src.core.dataset_collector import dataset_collector
import logging

logger = logging.getLogger(__name__)
router = Router(name="main_handlers")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "✈️ <b>Flight Helper Chatbot</b>\n\n"
        "Привет! Я помогу узнать информацию о рейсах.\n"
        "\n"
        "💬 Просто спросите:\n"
        "• «Статус рейса SU1234»\n"
        "• «Где находится борт S7123?»\n"
        "• «Вылетел ли рейс DP456?»\n"
        "\n"
        "📚 Или используйте команды:\n"
        "/help — справка по возможностям\n"
        "/about — информация о проекте",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "ℹ️ <b>Справка</b>\n\n"
        "<b>Как пользоваться:</b>\n"
        "Просто напишите запрос естественным языком:\n"
        "• «Статус рейса SU1234»\n"
        "• «Где борт S7123?»\n"
        "• «Вылетел ли DP456?»\n\n"
        "<b>Поддерживаемые авиакомпании:</b>\n"
        "• SU — Аэрофлот (пример: SU1234)\n"
        "• S7 — S7 Airlines (пример: S7123)\n"
        "• DP — Победа (пример: DP456)\n\n"
        "<b>Важно:</b>\n"
        "• Данные берутся из открытого источника OpenSky Network\n"
        "• Рейс должен быть в эфире (в воздухе или на ВПП)\n"
        "• Для точной информации обращайтесь к авиакомпании",
        parse_mode="HTML"
    )


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    await message.answer(
        "🎓 <b>О проекте</b>\n\n"
        "<b>Цель:</b> Обучение интеграции с внешними API и работе с естественным языком.\n\n"
        "<b>Технологии:</b>\n"
        "• Python 3.14.0\n"
        "• aiogram 3.12\n"
        "• OpenSky Network API (OAuth2)\n"
        "• Правило-ориентированная классификация интентов\n\n"
        "<b>Статус:</b>\n"
        "Учебный проект. Не связан с авиакомпаниями.\n\n"
        "<b>Исходный код:</b>\n"
        "https://github.com/ваш-логин/flight-helper-chatbot",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(Command("flight"))
async def cmd_flight(message: Message) -> None:
    """Обработчик команды /flight (для обратной совместимости)"""
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "🛫 Укажите номер рейса:\n<code>/flight SU1234</code>",
            parse_mode="HTML"
        )
        return

    flight_number = args[0].upper().strip()
    await _handle_flight_status(message, flight_number)


@router.message()
async def handle_natural_language(message: Message) -> None:
    """
    Основной обработчик для естественного языка.

    Логика:
    1. Распознаём интент (намерение пользователя)
    2. Извлекаем сущности (номер рейса)
    3. Выполняем соответствующее действие
    """
    if not message.text:
        await message.answer("💬 Я обрабатываю только текстовые сообщения.")
        return

    # Распознаём интент
    intent, entities = intent_service.detect_intent(message.text)

    if settings.DEBUG:
        logger.debug(f"Распознан интент: {intent.value} | Сущности: {entities} | Текст: '{message.text[:50]}'")

    # Обработка интентов
    if intent == Intent.FLIGHT_STATUS:
        flight_number = entities.get("flight_number")
        if flight_number:
            await _handle_flight_status(message, flight_number)
        else:
            await message.answer("⚠️ Не удалось извлечь номер рейса из запроса.")

    elif intent == Intent.HELP_REQUEST:
        await cmd_help(message)

    elif intent == Intent.ABOUT_REQUEST:
        await cmd_about(message)

    elif intent == Intent.GREETING:
        await message.answer(
            "👋 Здравствуйте!\n"
            "Я — Flight Helper Chatbot. Спросите меня о статусе рейса, например:\n"
            "«Статус рейса SU1234»"
        )

    elif intent == Intent.UNKNOWN:
        # Эхо с подсказкой
        await message.answer(
            f"🔁 Я получил ваше сообщение:\n\n{message.text}\n\n"
            "💡 Попробуйте спросить о рейсе:\n"
            "«Статус рейса SU1234»",
            parse_mode="HTML"
        )


@router.message(Command("dataset"))
async def cmd_dataset(message: Message) -> None:
    """Команда для просмотра статистики собранного датасета"""
    if not settings.DEBUG:
        await message.answer("⚠️ Эта команда доступна только в режиме отладки")
        return

    stats = dataset_collector.get_stats()
    response = (
        "📊 <b>Статистика датасета</b>\n\n"
        f"Всего образцов: {stats['total_samples']}\n"
        f"С данными о рейсе: {stats['with_flight_data']}\n"
        f"\nИнтенты:\n"
    )
    for intent, count in stats["intents"].items():
        response += f"• {intent}: {count}\n"

    response += "\n<i>Данные сохраняются локально в data/dataset.jsonl</i>"

    await message.answer(response, parse_mode="HTML")

async def _handle_flight_status(message: Message, flight_number: str) -> None:
    """Обработка запроса статуса рейса с сохранением данных для дообучения"""
    callsign = opensky_client.flight_number_to_callsign(flight_number)
    logger.info(f"Запрос статуса рейса: {flight_number} → callsign: {callsign}")

    flight_data = await opensky_client.get_flight_by_callsign(callsign)

    ai_response = await ai_client.generate_flight_status_response(
        flight_number=flight_number,
        flight_data=flight_data,
        user_question=message.text or ""
    )

    # Сохраняем образец для будущего дообучения
    if settings.DEBUG:
        dataset_collector.add_sample(
            user_query=message.text or "",
            bot_response=ai_response,
            flight_data=flight_data,
            intent="flight_status"
        )

    await message.answer(ai_response)