import allure
import pytest
import random
from datetime import datetime
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi

WORDS = [
    "альфа", "бета", "гамма", "дельта", "эпсилон", "зета", "эта", "тета",
    "йота", "каппа", "лямбда", "мю", "ню", "кси", "омикрон", "пи",
]


@pytest.mark.jira_integration
class TestJiraIntegration:

    @allure.title("Worklog отправленной в Ассистента записи появляется в Jira")
    def test_entry_worklog_appears_in_jira(self, vinny_api: VinnyApi, jira_api: JiraApi, test_task: str, api_error_handler):
        description = f"автотест: интеграционная проверка worklog {datetime.now().isoformat()} {random.choice(WORDS)}"
        with api_error_handler():
            with allure.step(f"Создать запись в ассистенте для задачи {test_task}, точный текст записи, созданной в Ассистенте: '{description}'"):
                vinny_api.create_entry_for_today(
                    task=test_task,
                    time_spent="15m",
                    description=description,
                )
            with allure.step(f"Запросить последний worklog задачи {test_task} напрямую из Jira"):
                last_worklog = jira_api.get_last_worklog(test_task)
        with allure.step(f"Проверить что worklog для {test_task} существует в Jira"):
            assert last_worklog is not None
        with allure.step(f"Проверить что описание записи в Ассистенте == комментарию worklog в Jira: '{description}' in '{last_worklog.comment}'"):
            assert description in last_worklog.comment
