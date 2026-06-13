import random
from datetime import datetime
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi

WORDS = [
    "альфа", "бета", "гамма", "дельта", "эпсилон", "зета", "эта", "тета",
    "йота", "каппа", "лямбда", "мю", "ню", "кси", "омикрон", "пи",
]


class TestJiraIntegration:

    def test_entry_worklog_appears_in_jira(self, vinny_api: VinnyApi, jira_api: JiraApi, test_task: str):
        description = f"автотест: интеграционная проверка worklog {datetime.now().isoformat()} {random.choice(WORDS)}"
        vinny_api.create_entry_for_today(
            task=test_task,
            time_spent="15m",
            description=description,
        )
        last_worklog = jira_api.get_last_worklog(test_task)
        assert last_worklog is not None
        assert description in last_worklog.comment
