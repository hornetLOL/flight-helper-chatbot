"""
Сервис классификации интентов (намерений пользователя).

Упрощённая архитектура (после анализа реальных запросов):
- Главный сигнал: наличие номера рейса в формате авиакомпании → всегда FLIGHT_STATUS
- Вторичные сигналы: ключевые слова для справки/приветствия
- Поддержка кириллицы в номерах рейсов (СУ → SU)
- Минимальная зависимость от контекста — максимум надёжности
"""
import re
from typing import Optional, Tuple, Dict
from enum import Enum

class Intent(Enum):
    """Типы распознанных намерений"""
    FLIGHT_STATUS = "flight_status"
    HELP_REQUEST = "help_request"
    GREETING = "greeting"
    ABOUT_REQUEST = "about_request"
    UNKNOWN = "unknown"


class IntentService:
    """Сервис распознавания интентов из текста"""

    def __init__(self):
        # Паттерн для номера рейса: 2 буквы (латиница или кириллица С/У) + 1-4 цифры
        # Поддерживаемые авиакомпании: Аэрофлот (SU/СУ), S7, Победа (DP)
        self.flight_number_pattern = re.compile(
            r"\b("
            r"[SС][UУ]\d{1,4}|"      # SU/СУ (Аэрофлот) — латиница и кириллица
            r"S7\d{1,4}|"             # S7 Airlines
            r"DP\d{1,4}|"             # Победа
            r"U6\d{1,4}|"             # Уральские авиалинии
            r"[A-Z]{2}\d{1,4}"        # Любой другой код авиакомпании
            r")\b",
            re.IGNORECASE
        )

        # Паттерны для справки (полное покрытие форм)
        self.help_patterns = [
            # Простые ключевые слова
            re.compile(r"\b(помощь|справка|команды)\b", re.IGNORECASE),
            # Вопросы о возможностях (все формы: ты/вы + умеешь/умеете/можешь/можете)
            re.compile(r"что (?:ты|вы) (?:умеешь|умеете|можешь|можете|делаешь|делаете)", re.IGNORECASE),
            re.compile(r"(?:какие|как) команды", re.IGNORECASE),
            re.compile(r"что я могу", re.IGNORECASE),
            # Английский
            re.compile(r"\b(help|commands|what can (you|I)|how to)\b", re.IGNORECASE),
        ]

        # Паттерны для приветствий (короткие сообщения)
        self.greeting_patterns = [
            re.compile(r"^(привет|здравствуй|добрый день|доброе утро|добрый вечер|хай|хеллоу|здравствуйте|прив|здарова)$", re.IGNORECASE),
            re.compile(r"^(hi|hello|hey|good morning|good afternoon|good evening|yo)$", re.IGNORECASE),
        ]

        # Паттерны для информации о проекте
        self.about_patterns = [
            re.compile(r"\b(о (боте|проекте|себе)|кто ты|что это|информация|проект)\b", re.IGNORECASE),
            re.compile(r"\b(about|info|who are you|project)\b", re.IGNORECASE),
        ]

    def detect_intent(self, text: str) -> Tuple[Intent, Dict[str, str]]:
        """
        Распознать интент и извлечь сущности из текста.

        Иерархия проверок (от самого надёжного сигнала):
        1. Наличие номера рейса → FLIGHT_STATUS (главный сигнал)
        2. Приветствие (короткие сообщения 1-3 слова)
        3. Справка / О проекте
        4. Неизвестный интент
        """
        text = text.strip()
        if not text:
            return Intent.UNKNOWN, {}

        # === ШАГ 1: Проверка на номер рейса (самый надёжный сигнал) ===
        # Нормализуем кириллицу в латиницу для кодов авиакомпаний
        normalized_text = self._normalize_flight_codes(text)
        match = self.flight_number_pattern.search(normalized_text)

        if match:
            flight_number = match.group(1).upper()
            # Финальная нормализация: кириллица → латиница
            flight_number = self._normalize_flight_codes(flight_number)
            return Intent.FLIGHT_STATUS, {"flight_number": flight_number}

        # === ШАГ 2: Короткие приветствия (1-3 слова) ===
        words = text.split()
        if len(words) <= 3:
            if any(pattern.fullmatch(text) for pattern in self.greeting_patterns):
                return Intent.GREETING, {}

        # === ШАГ 3: Проверка других интентов ===
        if any(pattern.search(text) for pattern in self.help_patterns):
            return Intent.HELP_REQUEST, {}

        if any(pattern.search(text) for pattern in self.about_patterns):
            return Intent.ABOUT_REQUEST, {}

        # === ШАГ 4: Приветствия в длинных сообщениях ===
        if any(pattern.search(text) for pattern in self.greeting_patterns):
            return Intent.GREETING, {}

        # === ШАГ 5: Неизвестный интент ===
        return Intent.UNKNOWN, {}

    def _normalize_flight_codes(self, text: str) -> str:
        """
        Нормализация кириллических символов в кодах авиакомпаний.

        Примеры:
        "СУ1234" → "SU1234"
        "борт СУ1234" → "борт SU1234"
        """
        # Заменяем кириллические С/У на латинские S/U только в контексте кодов авиакомпаний
        text = re.sub(r"СУ(\d)", r"SU\1", text)  # СУ1234 → SU1234
        text = re.sub(r"С7(\d)", r"S7\1", text)   # С7123 → S7123
        text = re.sub(r"ДП(\d)", r"DP\1", text)   # ДП456 → DP456
        return text

    def extract_flight_number(self, text: str) -> Optional[str]:
        """
        Извлечь номер рейса из текста.
        """
        intent, entities = self.detect_intent(text)
        if intent == Intent.FLIGHT_STATUS:
            return entities.get("flight_number")
        return None


# Глобальный экземпляр сервиса
intent_service = IntentService()