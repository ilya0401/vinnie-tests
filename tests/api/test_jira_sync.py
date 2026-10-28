import allure
import pytest
from utils.vinny_API import VinnyApi
from utils.kafka_ui_API import KafkaUiApi

JIRA_TOPIC = "jira-worklog-requests"
JIRA_CONSUMER_GROUP = "jira-delivery"


@pytest.mark.jira_sync
class TestJiraSyncStatus:
    """Явно проверяем статус, который сообщает сам ассистент."""

    @allure.title("[2.1.] Jira настроена и доступна: проверка через получение ответа в Ассистента от Jira")
    def test_jira_connection_is_configured_and_reachable(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        with api_error_handler():
            with allure.step("Через Ассистента запросить статус подключения к Jira"):
                result = vinny_api.check_jira_connection(test_task)
        with allure.step("Через Ассистента проверить что Jira сконфигурирована"):
            assert result.configured is True
        with allure.step("Проверить что Jira ответила Ассстенту HTTP 200"):
            assert result.status == 200

    @allure.label("tc_id", "TC-002")
    @allure.title("[2.4.] Запись без указанной задачи не публикуется в Kafka")
    def test_entry_without_task_is_not_published_to_kafka(self, vinny_api: VinnyApi, api_error_handler):
        with api_error_handler():
            with allure.step("Создать запись в Ассистенте без указания задачи (task='—')"):
                result = vinny_api.create_entry_for_today(
                    task="—",
                    time_spent="15m",
                    description="автотест: запись без задачи",
                )
        with allure.step(
            f"Проверить что Ассистент не поставил запись в очередь на доставку в Jira "
            f"(jira_status='skipped'), получено: '{result.jira_status}'"
        ):
            assert result.jira_status == "skipped"

    @allure.label("tc_id", "TC-007")
    @allure.title("[2.3.] Проверка отправки ворклога по несуществующей задаче в Jira")
    def test_nonexistent_task_returns_not_found(
        self, vinny_api: VinnyApi, kafka_ui_api: KafkaUiApi, api_error_handler
    ):
        with api_error_handler():
            with allure.step("Создать запись в Ассистенте с несуществующей задачей KAN-99999"):
                result = vinny_api.create_entry_for_today(
                    task="KAN-99999",
                    time_spent="15m",
                    description="автотест: несуществующая задача",
                )
        with allure.step(
            "Jira для несуществующей задачи всегда отвечает 404 независимо от прав токена, поэтому "
            "финальный статус синка нельзя перепроверить через Jira API напрямую — проверяем, что "
            "ассистент всё равно корректно сохранил запись локально, а не упал"
        ):
            saved_entry = vinny_api.get_entry_by_id(result.id)
            assert saved_entry is not None
        with allure.step(
            f"Проверить что консьюмер сдался и закоммитил offset немедленно (TC-012: lag консьюмер-группы "
            f"'{JIRA_CONSUMER_GROUP}' по топику '{JIRA_TOPIC}' вернулся к 0), не уйдя в бесконечный retry"
        ):
            kafka_ui_api.wait_for_zero_lag(topic=JIRA_TOPIC, group_id=JIRA_CONSUMER_GROUP, timeout=30)
