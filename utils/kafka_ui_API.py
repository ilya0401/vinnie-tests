import json

from utils.base_API import BaseApi
from utils.models.kafka_ui_models import ConsumerGroupInfo
from utils.wait import wait_until


class KafkaUiApi(BaseApi):
    """Читает состояние Kafka через REST API kafka-ui — без docker exec/сокета,
    поэтому работает одинаково локально и в Jenkins (оба в сети vinnie-network)."""

    def __init__(self, url: str, cluster: str):
        super().__init__(url)
        self.cluster = cluster

    def get_consumer_group_lag(self, topic: str, group_id: str) -> int | None:
        response = self.get(
            endpoint=f"/api/clusters/{self.cluster}/topics/{topic}/consumer-groups",
            model_type=list[ConsumerGroupInfo],
        )
        for group in response.data:
            if group.groupId == group_id:
                return group.consumerLag
        return None

    def wait_for_zero_lag(self, topic: str, group_id: str, timeout: float = 30, interval: float = 1) -> None:
        last_lag = None

        def _check():
            nonlocal last_lag
            last_lag = self.get_consumer_group_lag(topic=topic, group_id=group_id)
            return last_lag == 0

        if not wait_until(_check, timeout=timeout, interval=interval):
            raise AssertionError(
                f"Lag консьюмер-группы '{group_id}' по топику '{topic}' не вернулся к 0 "
                f"за {timeout}с (последнее значение: {last_lag})"
            )

    def get_latest_messages(self, topic: str, limit: int = 1) -> list[dict]:
        """Возвращает до `limit` последних сообщений топика (распарсенный payload каждого).
        Сообщения, чей value не парсится как JSON, пропускаются, а не роняют вызов —
        на будущих топиках формат может быть другим. Обычный /messages у этого форка
        kafka-ui отключён ("Not supported") — используется SSE-эндпоинт /messages/v2,
        отдающий построчные события "data: {...}"."""
        response = self.get(
            endpoint=f"/api/clusters/{self.cluster}/topics/{topic}/messages/v2",
            params={"mode": "LATEST", "limit": limit},
        )
        messages = []
        for line in response.raw.text.splitlines():
            if not line.startswith("data:"):
                continue
            event = json.loads(line[len("data:"):])
            if event.get("type") != "MESSAGE":
                continue
            try:
                messages.append(json.loads(event["message"]["value"]))
            except (json.JSONDecodeError, TypeError):
                continue
        return messages

    def get_latest_message(self, topic: str) -> dict | None:
        """Возвращает распарсенный payload последнего сообщения топика, либо None если
        топик пуст или его последнее сообщение не парсится как JSON."""
        messages = self.get_latest_messages(topic, limit=1)
        return messages[0] if messages else None

    def list_topics(self) -> list[str]:
        """Имена всех пользовательских (не internal, например __consumer_offsets) топиков кластера."""
        response = self.get(endpoint=f"/api/clusters/{self.cluster}/topics")
        return [t["name"] for t in response.raw.json()["topics"] if not t.get("internal")]

    def assert_entry_absent_from_other_topics(
        self, entry_id: int, exclude_topic: str, scan_limit: int = 50
    ) -> None:
        """Проверяет, что запись с этим entry_id не встречается среди последних `scan_limit`
        сообщений ни в одном пользовательском топике кластера, кроме `exclude_topic`. На
        случай будущих топиков с другой схемой — у них просто не будет поля entry_id,
        совпадения не найдётся, это не ошибка."""
        for topic in self.list_topics():
            if topic == exclude_topic:
                continue
            for message in self.get_latest_messages(topic, limit=scan_limit):
                if message.get("entry_id") == entry_id:
                    raise AssertionError(
                        f"entry_id={entry_id} найден в топике '{topic}', а должен быть "
                        f"только в '{exclude_topic}'"
                    )
