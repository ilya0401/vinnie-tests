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
    def test_entry_worklog_appears_in_jira(self, vinny_api: VinnyApi, jira_api: JiraApi, test_task: str):
        description = f"автотест: интеграционная проверка worklog {datetime.now().isoformat()} {random.choice(WORDS)}"
        with allure.step("Создать запись в ассистенте"):
            vinny_api.create_entry_for_today(
                task=test_task,
                time_spent="15m",
                description=description,
            )
        with allure.step("Запросить последний worklog по указанной из Jira напрямую"):
            last_worklog = jira_api.get_last_worklog(test_task)
        with allure.step("Проверить что worklog существует"):
            assert last_worklog is not None
        with allure.step("Проверить что текст в последнем комментарии (worklog) совпадает с отправленным"):
            assert description in last_worklog.comment
