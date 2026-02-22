"""
Клиент для работы с OpenSky Network API (OAuth2 аутентификация).

Важно:
- Параметр callsign НЕ поддерживается в запросе — фильтрация на стороне клиента
- Правильные индексы данных согласно документации OpenSky
- on_ground находится в индексе 8, а не 11
"""
import httpx
import logging
import time
from typing import Optional, Dict, Any, List
from src.core.config import settings

logger = logging.getLogger(__name__)


class OpenSkyClient:
    """Клиент для запросов к OpenSky Network API"""

    AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    API_BASE_URL = "https://opensky-network.org/api"

    def __init__(self):
        self.client_id = settings.OPENSKY_CLIENT_ID or ""
        self.client_secret = settings.OPENSKY_CLIENT_SECRET or ""
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0
        self.timeout = 15.0

        if not self.client_id or not self.client_secret:
            logger.warning(
                "⚠️  OpenSky OAuth2 credentials отсутствуют в .env\n"
                "   → Добавьте OPENSKY_CLIENT_ID и OPENSKY_CLIENT_SECRET в .env"
            )

    async def _get_access_token(self) -> Optional[str]:
        """Получить или обновить access token через OAuth2"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

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
                expires_in = token_data.get("expires_in", 1800)

                if not access_token:
                    logger.error("❌ OpenSky: access_token отсутствует в ответе авторизации")
                    return None

                self._access_token = access_token
                self._token_expires_at = time.time() + expires_in - 300

                if settings.DEBUG:
                    logger.info(f"✅ OpenSky: получен новый access token (действует до {time.ctime(self._token_expires_at)})")

                return access_token

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            logger.error(f"❌ OpenSky OAuth2 ошибка {status}")
            if status == 401:
                logger.error("   → Проверьте правильность OPENSKY_CLIENT_ID/SECRET в .env")
            return None
        except Exception as e:
            logger.error(f"❌ OpenSky OAuth2 исключение: {type(e).__name__}: {e}")
            return None

    async def get_flight_by_callsign(self, callsign: str) -> Optional[Dict[str, Any]]:
        """
        Получить данные о рейсе по-позывному (callsign).

        ВАЖНО: OpenSky не поддерживает фильтрацию по callsign в запросе.
        Мы получаем все рейсы и фильтруем на стороне клиента.
        """
        if not self.client_id or not self.client_secret:
            logger.warning("⚠️  OpenSky: OAuth2 credentials не настроены — возвращаю заглушку")
            return self._generate_mock_flight(callsign)

        access_token = await self._get_access_token()
        if not access_token:
            logger.error("❌ OpenSky: не удалось получить access token")
            return None

        url = f"{self.API_BASE_URL}/states/all"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "flight-helper-chatbot/1.0",
        }

        if settings.DEBUG:
            logger.debug(f"OpenSky request | url={url} | searching for callsign={callsign}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                # Автоматическое обновление токена при 401
                if response.status_code == 401:
                    logger.warning("⚠️  OpenSky: токен просрочен — пробую обновить")
                    self._access_token = None
                    access_token = await self._get_access_token()
                    if not access_token:
                        return None
                    headers["Authorization"] = f"Bearer {access_token}"
                    response = await client.get(url, headers=headers)

                response.raise_for_status()
                data = response.json()
                states = data.get("states", [])

                if settings.DEBUG:
                    logger.debug(f"OpenSky response | total_states={len(states)}")

                # 🔑 КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: фильтрация на стороне клиента
                for state in states:
                    if not state or len(state) < 2:
                        continue

                    # Callsign находится в индексе 1
                    state_callsign = state[1]
                    if state_callsign and state_callsign.strip().upper() == callsign.upper().strip():
                        logger.info(f"✅ Найден рейс {callsign} в эфире")
                        return self._parse_state(state, callsign)

                logger.info(f"⚠️  Рейс {callsign} не найден в эфире (получено {len(states)} рейсов)")
                return None

        except httpx.HTTPStatusError as e:
            logger.error(f"❌ OpenSky API ошибка {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка OpenSky: {type(e).__name__}: {e}")
            return None

    def _parse_state(self, state: list, callsign: str) -> Dict[str, Any]:
        """
        Парсинг сырых данных от OpenSky в читаемый формат.

        Согласно документации (индексы массива):
        0: icao24
        1: callsign
        2: origin_country
        3: time_position
        4: last_contact
        5: longitude
        6: latitude
        7: baro_altitude
        8: on_ground ← КРИТИЧЕСКИ ВАЖНО!
        9: velocity
        10: true_track
        11: vertical_rate
        12: sensors
        13: geo_altitude
        14: squawk
        15: spi
        16: position_source
        17: category
        """
        return {
            "callsign": callsign.upper().strip(),
            "icao24": state[0] if len(state) > 0 and state[0] else "N/A",
            "origin_country": state[2] if len(state) > 2 and state[2] else "Неизвестно",
            "on_ground": bool(state[8]) if len(state) > 8 and state[8] is not None else False,  # ← ИСПРАВЛЕНО: индекс 8
            "altitude_m": int(state[7]) if len(state) > 7 and state[7] else 0,  # ← ИСПРАВЛЕНО: индекс 7
            "velocity_kmh": int(state[9] * 3.6) if len(state) > 9 and state[9] else 0,  # ← ИСПРАВЛЕНО: индекс 9
            "vertical_speed": int(state[11]) if len(state) > 11 and state[11] is not None else 0,
            "heading": int(state[10]) if len(state) > 10 and state[10] is not None else 0,
            "last_contact_sec": state[4] if len(state) > 4 and state[4] else 0,
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
        """Синтетические данные для обучения"""
        import random
        is_airborne = random.choice([True, False])
        return {
            "callsign": callsign.upper().strip(),
            "icao24": f"{''.join(random.choices('0123456789ABCDEF', k=6))}",
            "origin_country": random.choice(["Россия", "Германия", "Турция", "ОАЭ"]),
            "on_ground": not is_airborne,
            "altitude_m": random.randint(8000, 12000) if is_airborne else 0,
            "velocity_kmh": random.randint(750, 900) if is_airborne else 0,
            "vertical_speed": random.choice([-5, 0, 5]) if is_airborne else 0,
            "heading": random.randint(0, 360),
            "last_contact_sec": int(time.time()),
        }


# Глобальный экземпляр клиента
opensky_client = OpenSkyClient()