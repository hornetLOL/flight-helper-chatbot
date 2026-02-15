"""
Конфигурация flight-helper-chatbot.
Загружает переменные из .env файла.
"""
from dotenv import load_dotenv
import os

# Загружаем переменные из .env при импорте модуля
load_dotenv()

class Settings:
    """Настройки приложения"""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    def validate(self) -> bool:
        """Проверка обязательных параметров"""
        if not self.BOT_TOKEN:
            print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
            print("   → Откройте .env и вставьте токен от @BotFather")
            print("   → Инструкция: https://core.telegram.org/bots#6-botfather")
            return False
        return True

# Единый экземпляр настроек для всего приложения
settings = Settings()