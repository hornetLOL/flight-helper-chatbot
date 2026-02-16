"""
Тесты для эхо-обработчика.

Проверяем:
- Обработку текстовых сообщений
- Отказ от обработки медиа (фото, видео)
- Форматирование ответа
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat
from src.bot.handlers import echo_handler


@pytest.mark.asyncio
async def test_echo_handler_text_message():
    """Тест: эхо для текстового сообщения"""
    # Подготовка мок-объекта сообщения
    message = MagicMock(spec=Message)
    message.text = "Привет, бот!"
    message.from_user = User(id=12345, is_bot=False, first_name="Test")
    message.chat = Chat(id=67890, type="private")
    message.answer = AsyncMock()

    # Вызов тестируемой функции
    await echo_handler(message)

    # Проверка вызова answer с правильным текстом
    message.answer.assert_called_once()
    call_args = message.answer.call_args
    assert "Привет, бот!" in call_args[0][0]  # Проверяем, что текст в ответе
    assert call_args[1]["parse_mode"] == "HTML"


@pytest.mark.asyncio
async def test_echo_handler_non_text_message():
    """Тест: отказ от обработки не-текстовых сообщений"""
    # Подготовка мок-объекта без текста (например, фото)
    message = MagicMock(spec=Message)
    message.text = None  # Нет текста
    message.from_user = User(id=12345, is_bot=False, first_name="Test")
    message.chat = Chat(id=67890, type="private")
    message.answer = AsyncMock()

    # Вызов тестируемой функции
    await echo_handler(message)

    # Проверка: бот предложил отправить текст/команду
    message.answer.assert_called_once()
    call_args = message.answer.call_args[0][0]
    assert "только текстовые сообщения" in call_args.lower()
    assert "/help" in call_args
    assert "/about" in call_args