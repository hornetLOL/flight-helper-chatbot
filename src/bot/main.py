"""
✈️ Flight Helper Chatbot — эхо-бот (Этап 1)

Учебный проект для изучения разработки чат-ботов и ИИ.
НЕ является официальным продуктом Аэрофлота или любой авиакомпании.

Функционал этапа 1:
- Команда /start — приветственное сообщение
- Эхо — повторяет любое текстовое сообщение
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from src.core.config import settings

# ======================
# Настройка логирования
# ======================
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ======================
# Инициализация компонентов
# ======================
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
router = Router()


# ======================
# Обработчики команд и сообщений
# ======================

@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """
    Обработчик команды /start

    Показывает приветственное сообщение с описанием возможностей бота.
    """
    await message.answer(
        "✈️ <b>Flight Helper Chatbot</b>\n\n"
        "Привет! Я — учебный ассистент для помощи с авиаперелётами.\n"
        "Пока я умею только повторять ваши сообщения (режим эхо).\n"
        "\n"
        "⚠️ <i>Это учебный проект. Не является продуктом Аэрофлота.</i>\n"
        "📚 Этап обучения: 1/6 — базовый эхо-бот",
        parse_mode="HTML"
    )
    logger.info(f"Пользователь {message.from_user.id} (@{message.from_user.username}) запустил бота")


@router.message()
async def echo_handler(message: Message) -> None:
    """
    Эхо-обработчик

    Повторяет любое текстовое сообщение пользователя.
    Игнорирует медиа (фото, видео) — обрабатываем только текст.
    """
    # Обрабатываем только текстовые сообщения
    if not message.text:
        await message.answer("💬 Я пока умею обрабатывать только текстовые сообщения.")
        return

    try:
        # Просто отправляем обратно то же сообщение
        await message.answer(
            f"🔁 Вы написали:\n\n{message.text}",
            parse_mode=None  # Без HTML чтобы избежать ошибок с пользовательским вводом
        )
        logger.debug(f"Эхо для {message.from_user.id}: {message.text[:50]}...")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от {message.from_user.id}: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")


# ======================
# Регистрация роутеров
# ======================
dp.include_router(router)


# ======================
# Точка входа в приложение
# ======================
async def main() -> None:
    """Основная функция запуска бота"""
    # Валидация конфигурации
    if not settings.validate():
        logger.critical("Конфигурация невалидна. Завершение работы.")
        return

    logger.info("=" * 50)
    logger.info("🚀 Flight Helper Chatbot запускается...")
    logger.info(f"   Python: {sys.version.split()[0]}")
    logger.info(f"   aiogram: 3.12.0")
    logger.info(f"   Режим отладки: {'ВКЛ' if settings.DEBUG else 'ВЫКЛ'}")
    logger.info("=" * 50)

    # Запуск поллинга
    await dp.start_polling(bot)


# ======================
# Обработка запуска скрипта
# ======================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем (Ctrl+C)")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)