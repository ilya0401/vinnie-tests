import allure
import pytest
from datetime import datetime
from utils.vinny_API import VinnyApi


@pytest.mark.jira_sync
class TestJiraSync:

    @allure.title("[2.1.] Jira настроена и доступна: проверка через получение ответа в Ассистента от Jira")
    def test_jira_connection_is_configured_and_reachable(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        with api_error_handler():
            with allure.step("Через Ассистента запросить статус подключения к Jira"):
                result = vinny_api.check_jira_connection(test_task)
        with allure.step("Через Ассистента проверить что Jira сконфигурирована"):
            assert result.configured is True
        with allure.step("Проверить что Jira ответила Ассстенту HTTP 200"):
            assert result.status == 200

    @allure.title("[2.2.] Создание записи в ассистенте, отправка записи в Jira, проверка ответа от Jira что ассистент успешно "
                  "записал worklog в Jira")
    def test_create_entry_logs_to_jira(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        description = f"автотест: проверка логирования в Jira [{datetime.now().isoformat()}]"
        with api_error_handler():
            with allure.step(f"Создать запись для задачи {test_task}: '{description}'"):
                result = vinny_api.create_entry_for_today(
                    task=test_task,
                    time_spent="15m",
                    description=description,
                )
        with allure.step(f"Проверить что ассистент успешно отправил worklog в Jira для {test_task}: jira_status == 'ok' (получено: '{result.jira_status}')"):
            assert result.jira_status == "ok"

    @allure.title("[2.3.] Проверка отправки ворклога по несуществующей задаче в Jira")
    def test_nonexistent_task_returns_not_found(self, vinny_api: VinnyApi, api_error_handler):
        with api_error_handler():
            with allure.step("Создать запись в Ассистенте с несуществующей задачей KAN-99999"):
                result = vinny_api.create_entry_for_today(
                    task="KAN-99999",
                    time_spent="15m",
                    description="автотест: несуществующая задача",
                )
        with allure.step("Проверить что запись в Jira не создалась, jira_status == not_found"):
            assert result.jira_status == "not_found"
