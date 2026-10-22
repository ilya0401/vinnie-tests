import os
import subprocess

from utils.wait import wait_until

DEFAULT_GROUP = "jira-delivery"
DEFAULT_TOPIC = "jira-worklog-requests"


def get_consumer_group_lag(group: str = DEFAULT_GROUP, topic: str = DEFAULT_TOPIC) -> int:
    """Суммарный lag consumer-группы по топику — через kafka-consumer-groups.sh внутри
    брокерского контейнера (проще и честнее, чем тянуть отдельный Kafka-клиент в vinnie-tests
    ради одной метрики, которую мы и так весь день читали руками тем же способом)."""
    container = os.getenv("KAFKA_CONTAINER", "vinnie-assistant-kafka-1")
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    result = subprocess.run(
        [
            "docker", "exec", container,
            "/opt/kafka/bin/kafka-consumer-groups.sh",
            "--bootstrap-server", bootstrap,
            "--describe", "--group", group,
        ],
        capture_output=True, text=True, timeout=15,
    )
    lag_total = 0
    for line in result.stdout.splitlines():
        parts = line.split()
        # GROUP TOPIC PARTITION CURRENT-OFFSET LOG-END-OFFSET LAG CONSUMER-ID HOST CLIENT-ID
        if len(parts) >= 6 and parts[0] == group and parts[1] == topic:
            lag_total += int(parts[5])
    return lag_total


def wait_for_zero_lag(group: str = DEFAULT_GROUP, topic: str = DEFAULT_TOPIC, timeout: float = 30, interval: float = 1) -> int:
    """Дожидается, пока consumer разберёт очередь (lag == 0) или таймаут. Возвращает
    финальный lag — вызывающий тест сам решает, что с ним делать (assert == 0 и т.п.)."""
    def _zero_or_none():
        lag = get_consumer_group_lag(group, topic)
        return True if lag == 0 else None

    wait_until(_zero_or_none, timeout=timeout, interval=interval)
    return get_consumer_group_lag(group, topic)
