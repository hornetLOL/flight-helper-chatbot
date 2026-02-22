"""
Простой клиент для генерации ответов без внешних зависимостей.
Использует шаблонные ответы с элементами естественности.
Подготовлен для будущего дообучения в Этапе 6.
"""
import logging
from typing import Optional, Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)


class AIClient:
    """Клиент для генерации ответов (заглушка для Этапа 5)"""

    def __init__(self):
        self.enabled = True
        logger.info("✅ Простой ИИ-клиент инициализирован (без внешних зависимостей)")

    async def generate_flight_status_response(
        self,
        flight_number: str,
        flight_data: Optional[Dict[str, Any]],
        user_question: str
    ) -> str:
        """
        Сгенерировать естественный ответ о статусе рейса.
        Использует шаблонные ответы с вариациями для естественности.
        """
        # Вариации ответов для естественности
        in_air_responses = [
            "✈️ Рейс {number} сейчас в воздухе на высоте {altitude} м. Скорость: {velocity} км/ч.",
            "🛫 Рейс {number} находится в полёте. Высота: {altitude} м, скорость {velocity} км/ч.",
            "🚀 Рейс {number} в небе! Текущая высота: {altitude} м, скорость: {velocity} км/ч."
        ]

        on_ground_responses = [
            "🛬 Рейс {number} находится на земле.",
            "🛬 Рейс {number} приземлился или готовится к вылету.",
            "🛬 Рейс {number} сейчас на ВПП."
        ]

        not_found_responses = [
            "⚠️ Рейс {number} не обнаружен в эфире в данный момент.",
            "⚠️ Данные о рейсе {number} временно недоступны.",
            "⚠️ Рейс {number} не найден в системе наблюдения."
        ]

        import random

        if flight_data:
            altitude = flight_data.get("altitude_m", 0)
            velocity = flight_data.get("velocity_kmh", 0)
            on_ground = flight_data.get("on_ground", False)

            if on_ground:
                template = random.choice(on_ground_responses)
                return template.format(number=flight_number)
            else:
                template = random.choice(in_air_responses)
                return template.format(
                    number=flight_number,
                    altitude=altitude,
                    velocity=velocity
                )
        else:
            template = random.choice(not_found_responses)
            return template.format(number=flight_number)


# Глобальный экземпляр клиента
ai_client = AIClient()