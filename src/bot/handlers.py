"""
Обработчики команд и сообщений для flight-helper-chatbot.

Архитектурный принцип:
- Каждая команда/сценарий — отдельная функция
- Обработчики не содержат бизнес-логику (только оркестрация)
- Импортируют сервисы из src.core для сложной логики
"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

router = Router(name="main_handlers")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Обработчик команды /start"""
    await message.answer(
        "✈️ <b>Flight Helper Chatbot</b>\n\n"
        "Привет! Я — учебный ассистент для помощи с авиаперелётами.\n"
        "Пока я нахожусь на этапе обучения и умею не всё.\n"
        "\n"
        "📚 Доступные команды:\n"
        "/help — справка по возможностям\n"
        "/about — информация о проекте\n"
        "/flight — заглушка для будущего функционала (статус рейса)\n"
        "\n"
        "⚠️ <i>Это учебный проект. Не является продуктом Аэрофлота.</i>",
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Обработчик команды /help"""
    await message.answer(
        "ℹ️ <b>Справка по возможностям</b>\n\n"
        "<b>Текущий этап разработки:</b> 2/6\n\n"
        "<b>Что умею сейчас:</b>\n"
        "• Отвечать на команды /start, /help, /about\n"
        "• Режим эхо для текстовых сообщений\n"
        "• Заглушка под запрос статуса рейса (/flight)\n\n"
        "<b>Что будет добавлено позже:</b>\n"
        "• Интеграция с авиационными API (статус рейсов)\n"
        "• Интент-классификация (понимание запросов)\n"
        "• Интеграция с ИИ-моделями для генерации ответов\n\n"
        "<b>Как пользоваться:</b>\n"
        "Просто отправьте команду или текстовое сообщение.\n"
        "Пример: <code>/flight SU1234</code>",
        parse_mode="HTML"
    )


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    """Обработчик команды /about"""
    await message.answer(
        "🎓 <b>О проекте Flight Helper Chatbot</b>\n\n"
        "<b>Цель:</b> Обучение разработке чат-ботов и работе с ИИ.\n\n"
        "<b>Технологии:</b>\n"
        "• Python 3.14.0\n"
        "• aiogram 3.12 (Telegram Bot API)\n"
        "• Планируется: AviationStack API, OpenRouter, Qwen2\n\n"
        "<b>Статус:</b>\n"
        "Учебный проект. Не связан с Аэрофлотом или другими авиакомпаниями.\n\n"
        "<b>Исходный код:</b>\n"
        "https://github.com/hornetLOL/flight-helper-chatbot\n\n"
        "<b>Лицензия:</b>\n"
        "MIT License",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(Command("flight"))
async def cmd_flight(message: Message) -> None:
    """
    Заглушка под будущую команду статуса рейса.

    На этом этапе показываем пользователю, что функционал в разработке,
    и объясняем формат будущего запроса.
    """
    # Извлекаем аргументы команды (номер рейса)
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if not args:
        await message.answer(
            "🛫 <b>Статус рейса (заглушка)</b>\n\n"
            "Этот функционал находится в разработке.\n"
            "Позже вы сможете проверить статус рейса по номеру.\n\n"
            "<b>Формат использования:</b>\n"
            "<code>/flight SU1234</code>\n\n"
            "<b>Поддерживаемые авиакомпании:</b>\n"
            "• SU — Аэрофлот\n"
            "• другие — через открытые авиационные API",
            parse_mode="HTML"
        )
        return

    flight_number = " ".join(args).upper()
    await message.answer(
        f"🚧 <b>Режим разработки</b>\n\n"
        f"Запрос статуса рейса: <code>{flight_number}</code>\n\n"
        "Функционал ещё не реализован.\n"
        "Это заглушка для будущей интеграции с авиационными API.\n\n"
        "Следите за прогрессом в репозитории:\n"
        "https://github.com/hornetLOL/flight-helper-chatbot",
        parse_mode="HTML"
    )


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Эхо-обработчик для текстовых сообщений.

    Игнорирует медиа (фото, видео, документы) — обрабатываем только текст.
    """
    if not message.text:
        await message.answer(
            "💬 Я пока умею обрабатывать только текстовые сообщения.\n"
            "Попробуйте отправить команду:\n"
            "/help — справка\n"
            "/about — о проекте"
        )
        return

    await message.answer(
        f"🔁 <b>Эхо:</b>\n\n{message.text}",
        parse_mode="HTML"
    )