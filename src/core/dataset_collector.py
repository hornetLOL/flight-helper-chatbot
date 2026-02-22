"""
Сборщик датасета для будущего дообучения.
Анонимизирует запросы и сохраняет только структурированные данные.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DatasetCollector:
    """Сборщик датасета с анонимизацией"""

    def __init__(self, dataset_path: str = "data/dataset.jsonl"):
        self.dataset_path = Path(dataset_path)
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        self.samples = []

        # Загружаем существующий датасет
        if self.dataset_path.exists():
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.samples.append(json.loads(line))

        logger.info(f"Загружено {len(self.samples)} образцов из {self.dataset_path}")

    def add_sample(
        self,
        user_query: str,
        bot_response: str,
        flight_data: Optional[Dict[str, Any]] = None,
        intent: str = "unknown"
    ) -> None:
        """Добавить анонимизированный образец в датасет"""
        # Простая анонимизация (удаляем потенциально личные данные)
        anonymized_query = self._anonymize_text(user_query)

        sample = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_query": anonymized_query,
            "bot_response": bot_response,
            "intent": intent,
            "has_flight_data": bool(flight_data),
            "flight_country": flight_data.get("origin_country", "unknown") if flight_data else "unknown",
            "on_ground": flight_data.get("on_ground", False) if flight_data else False,
            "altitude_m": flight_data.get("altitude_m", 0) if flight_data else 0,
            "velocity_kmh": flight_data.get("velocity_kmh", 0) if flight_data else 0,
        }

        self.samples.append(sample)

        # Сохраняем сразу (для надёжности)
        with open(self.dataset_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

        if len(self.samples) % 10 == 0:
            logger.info(f"Собрано {len(self.samples)} образцов для дообучения")

    def _anonymize_text(self, text: str) -> str:
        """Удаляем потенциально личные данные"""
        import re
        # Удаляем номера телефонов
        text = re.sub(r"\+?\d[\d\s\-\(\)]{8,}", "[ТЕЛЕФОН]", text)
        # Удаляем email
        text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text)
        return text

    def get_stats(self) -> Dict[str, Any]:
        """Статистика по датасету"""
        intents = {}
        for sample in self.samples:
            intent = sample["intent"]
            intents[intent] = intents.get(intent, 0) + 1

        return {
            "total_samples": len(self.samples),
            "intents": intents,
            "with_flight_data": sum(1 for s in self.samples if s["has_flight_data"]),
        }


# Глобальный экземпляр
dataset_collector = DatasetCollector()