"""
Конфигурация приложения.
Загружает переменные из .env файла.
"""
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()


class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    def validate(self) -> bool:
        """Проверка обязательных параметров"""
        if not self.BOT_TOKEN:
            print("Ошибка: BOT_TOKEN не найден в .env файле")
            print("   → Скопируйте .env.example в .env и вставьте токен от @BotFather")
            return False
        return True


# Единый экземпляр настроек
settings = Settings()