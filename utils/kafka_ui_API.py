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
