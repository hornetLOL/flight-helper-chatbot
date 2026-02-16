"""
✈️ Flight Helper Chatbot — точка входа (Этап 2)

Архитектура:
- Инициализация бота и диспетчера
- Подключение роутеров из handlers.py
- Запуск поллинга
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from src.bot.handlers import router
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
# Точка входа в приложение
# ======================
async def main() -> None:
    """Основная функция запуска бота"""
    # Валидация конфигурации
    if not settings.validate():
        logger.critical("Конфигурация невалидна. Завершение работы.")
        return

    # Инициализация бота
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    # Подключение роутеров
    dp.include_router(router)

    logger.info("=" * 50)
    logger.info("🚀 Flight Helper Chatbot запускается...")
    logger.info(f"   Python: {sys.version.split()[0]}")
    logger.info(f"   aiogram: 3.12.0")
    logger.info(f"   Этап: 2/6 — расширенный функционал")
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
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
        sys.exit(1)