"""
Тесты для сервиса классификации интентов.
Фокус на реальных пользовательских запросах.
"""
import pytest
from src.core.intent_service import IntentService, Intent

@pytest.fixture
def service():
    return IntentService()

def test_flight_status_with_flight_number(service):
    """Тест: любой запрос с номером рейса → FLIGHT_STATUS"""
    test_cases = [
        # Русский с кириллицей в коде
        ("где борт СУ1234?", Intent.FLIGHT_STATUS, "SU1234"),
        ("Статус рейса СУ1234", Intent.FLIGHT_STATUS, "SU1234"),
        ("борт С7123 где?", Intent.FLIGHT_STATUS, "S7123"),
        ("ДП456 вылетел?", Intent.FLIGHT_STATUS, "DP456"),

        # Русский с латиницей
        ("где борт S7123?", Intent.FLIGHT_STATUS, "S7123"),
        ("Статус рейса SU1234", Intent.FLIGHT_STATUS, "SU1234"),
        ("Вылетел ли рейс DP456?", Intent.FLIGHT_STATUS, "DP456"),
        ("SU1234", Intent.FLIGHT_STATUS, "SU1234"),
        ("S7123 где?", Intent.FLIGHT_STATUS, "S7123"),
        ("U6789", Intent.FLIGHT_STATUS, "U6789"),

        # Английский
        ("Flight status SU1234", Intent.FLIGHT_STATUS, "SU1234"),
        ("Where is aircraft S7123?", Intent.FLIGHT_STATUS, "S7123"),
        ("Has DP456 departed?", Intent.FLIGHT_STATUS, "DP456"),
        ("SU1234 altitude", Intent.FLIGHT_STATUS, "SU1234"),

        # Смешанный язык
        ("Где SU1234?", Intent.FLIGHT_STATUS, "SU1234"),
        ("S7123 статус", Intent.FLIGHT_STATUS, "S7123"),
    ]

    for text, expected_intent, expected_flight in test_cases:
        intent, entities = service.detect_intent(text)
        assert intent == expected_intent, f"Для '{text}' ожидался {expected_intent}, получен {intent}"
        assert entities.get("flight_number") == expected_flight, \
            f"Для '{text}' ожидался номер {expected_flight}, получен {entities.get('flight_number')}"

def test_help_intent(service):
    """Тест: запросы справки"""
    test_cases = [
        ("Помощь", Intent.HELP_REQUEST),
        ("Что ты умеешь?", Intent.HELP_REQUEST),
        ("Что вы можете?", Intent.HELP_REQUEST),
        ("команды", Intent.HELP_REQUEST),
        ("help", Intent.HELP_REQUEST),
        ("what can you do", Intent.HELP_REQUEST),
    ]

    for text, expected_intent in test_cases:
        intent, _ = service.detect_intent(text)
        assert intent == expected_intent, f"Для '{text}' ожидался {expected_intent}, получен {intent}"

def test_greeting_intent(service):
    """Тест: приветствия"""
    test_cases = [
        ("Привет", Intent.GREETING),
        ("Здравствуй", Intent.GREETING),
        ("Добрый день", Intent.GREETING),
        ("hi", Intent.GREETING),
        ("hello", Intent.GREETING),
        ("прив", Intent.GREETING),
    ]

    for text, expected_intent in test_cases:
        intent, _ = service.detect_intent(text)
        assert intent == expected_intent, f"Для '{text}' ожидался {expected_intent}, получен {intent}"

def test_about_intent(service):
    """Тест: запросы об информации о проекте"""
    test_cases = [
        ("о боте", Intent.ABOUT_REQUEST),
        ("кто ты?", Intent.ABOUT_REQUEST),
        ("о проекте", Intent.ABOUT_REQUEST),
        ("about", Intent.ABOUT_REQUEST),
    ]

    for text, expected_intent in test_cases:
        intent, _ = service.detect_intent(text)
        assert intent == expected_intent, f"Для '{text}' ожидался {expected_intent}, получен {intent}"

def test_unknown_intent(service):
    """Тест: нераспознанные запросы без номера рейса"""
    test_cases = [
        "Как погода сегодня?",
        "Расскажи анекдот",
        "12345",  # Невалидный номер рейса
        "Москва",  # Город, не рейс
        "Хочу пиццу",
    ]

    for text in test_cases:
        intent, _ = service.detect_intent(text)
        assert intent == Intent.UNKNOWN, f"Для '{text}' ожидался UNKNOWN, получен {intent}"