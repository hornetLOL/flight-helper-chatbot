"""
Клиент для работы с OpenSky Network API (OAuth2 аутентификация).

Важно для аккаунтов после марта 2025:
- Базовая аутентификация (логин/пароль) НЕ РАБОТАЕТ
- Требуется OAuth2 Client Credentials Flow
- Токен живёт 30 минут → нужна автоматическая перегенерация

Документация: https://openskynetwork.github.io/opensky-api/rest.html
"""
import httpx
import logging
import time
from typing import Optional, Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)


class OpenSkyOAuth2Client:
    """Клиент с поддержкой OAuth2 аутентификации"""

    AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    API_BASE_URL = "https://opensky-network.org/api"

    def __init__(self):
        self.client_id = settings.OPENSKY_CLIENT_ID or ""
        self.client_secret = settings.OPENSKY_CLIENT_SECRET or ""
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self.timeout = 15.0

        # Валидация конфигурации
        if not self.client_id or not self.client_secret:
            logger.warning(
                "⚠️  OpenSky OAuth2 credentials отсутствуют в .env\n"
                "   → Добавьте OPENSKY_CLIENT_ID и OPENSKY_CLIENT_SECRET в .env\n"
                "   → Инструкция: Account Settings → API Clients → Create new API client"
            )

    async def _get_access_token(self) -> Optional[str]:
        """
        Получить или обновить access token через OAuth2.

        Токен кэшируется на 25 минут (из 30) для избежания просрочки.
        """
        # Проверяем, не истёк ли текущий токен
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        # Формируем запрос на получение токена
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.AUTH_URL,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()

                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 1800)  # 30 минут по умолчанию

                if not access_token:
                    logger.error("❌ OpenSky: access_token отсутствует в ответе авторизации")
                    return None

                # Кэшируем токен с запасом 5 минут
                self._access_token = access_token
                self._token_expires_at = time.time() + expires_in - 300

                if settings.DEBUG:
                    logger.info(f"✅ OpenSky: получен новый access token (действует до {time.ctime(self._token_expires_at)})")

                return access_token

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:300]
            logger.error(f"❌ OpenSky OAuth2 ошибка {status}: {text}")

            # Специальная диагностика для 401
            if status == 401:
                logger.error(
                    "   Возможные причины 401 при получении токена:\n"
                    "   • Неправильный CLIENT_ID или CLIENT_SECRET в .env\n"
                    "   • CLIENT_SECRET скопирован не полностью (показывается ОДИН РАЗ)\n"
                    "   • Тип клиента должен быть 'confidential'\n"
                    "   → Совет: пересоздайте API client и скопируйте секрет заново"
                )
            return None
        except Exception as e:
            logger.error(f"❌ OpenSky OAuth2 исключение: {type(e).__name__}: {e}")
            return None

    async def get_flight_by_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """
        Получить данные о рейсе по позывному через OAuth2.
        """
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️  OpenSky: OAuth2 credentials не настроены — возвращаю заглушку")
            return self._generate_mock_flight(callsign)

        access_token = await self._get_access_token()
        if not access_token:
            logger.error("❌ OpenSky: не удалось получить access token — запрос отменён")
            return None

        url = f"{self.API_BASE_URL}/states/all"
        params = {"callsign": callsign.strip()}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "flight-helper-chatbot/1.0 (Python httpx)",
            "Accept": "application/json",
        }

        if settings.DEBUG:
            logger.debug(f"OpenSky OAuth2 request | callsign={callsign}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)

                # Автоматическое обновление токена при 401
                if response.status_code == 401:
                    logger.warning("⚠️  OpenSky: токен просрочен — пробую обновить")
                    self._access_token = None  # Сбрасываем кэш
                    access_token = await self._get_access_token()
                    if not access_token:
                        return None
                    # Повторяем запрос с новым токеном
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = await client.get(url, params=params, headers=headers)

                response.raise_for_status()
                data = response.json()
                states = data.get("states", [])

                if not states:
                    logger.info(f"Рейс {callsign} не найден в эфире (аутентификация успешна)")
                    return None

                return self._parse_state(states[0], callsign)

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:300]
            logger.error(f"❌ OpenSky API ошибка {status}: {text}")
            return None
        except httpx.ConnectTimeout:
            logger.warning("⚠️  Таймаут подключения к OpenSky API")
            return None
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка OpenSky: {type(e).__name__}: {e}")
            return None

    def _parse_state(self, state: list, callsign: str) -> Dict[str, Any]:
        """Парсинг сырых данных от OpenSky в читаемый формат"""
        if len(state) < 19:
            logger.warning(f"Неполные данные от OpenSky для {callsign}")
            return self._generate_mock_flight(callsign)

        return {
            "callsign": callsign.upper().strip(),
            "icao24": state[0] if state[0] else "N/A",
            "origin_country": state[5] if state[5] else "Неизвестно",
            "on_ground": bool(state[11]) if state[11] is not None else False,
            "altitude_m": int(state[10]) if state[10] else 0,
            "velocity_kmh": int(state[13] * 3.6) if state[13] else 0,
            "vertical_speed": int(state[16]) if state[16] is not None else 0,
            "heading": int(state[18]) if state[18] is not None else 0,
            "last_contact_sec": state[7] if state[7] else 0,
        }

    @staticmethod
    def flight_number_to_callsign(flight_number: str) -> str:
        """Преобразование номера рейса в callsign (учебная заглушка)"""
        flight_number = flight_number.upper().replace(" ", "")
        if flight_number.startswith("SU"):
            return f"AFL{flight_number[2:]}"
        elif flight_number.startswith("S7"):
            return f"SBI{flight_number[2:]}"
        elif flight_number.startswith("DP"):
            return f"UTA{flight_number[2:]}"
        else:
            return flight_number

    @staticmethod
    def _generate_mock_flight(callsign: str) -> Dict[str, Any]:
        """Синтетические данные для обучения (когда API недоступен)"""
        import random
        is_airborne = random.choice([True, False])
        return {
            "callsign": callsign.upper().strip(),
            "icao24": f"{''.join(random.choices('0123456789ABCDEF', k=6))}",
            "origin_country": random.choice(["Россия", "Германия", "Турция", "ОАЭ", "Китай"]),
            "on_ground": not is_airborne,
            "altitude_m": random.randint(8000, 12000) if is_airborne else 0,
            "velocity_kmh": random.randint(750, 900) if is_airborne else 0,
            "vertical_speed": random.choice([-5, 0, 5]) if is_airborne else 0,
            "heading": random.randint(0, 360),
            "last_contact_sec": int(time.time()),
        }


# Глобальный экземпляр клиента
opensky_client = OpenSkyOAuth2Client()