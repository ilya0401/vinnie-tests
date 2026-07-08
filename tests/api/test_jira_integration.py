import allure
import pytest
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi


@pytest.mark.jira_integration
class TestJiraIntegration:

    @pytest.mark.parametrize(
        "task_number, time_spent, description",
        [
            pytest.param(7, "1h 45m", "тестовый дескрипшн, параметризация, позитивный кейс 1", id="task_7"),
            pytest.param(9, "30m", "тестовый дескрипшн, параметризация, позитивный кейс 2", id="task_9"),
        ],
    )
    @allure.title("[3.1.] Worklog отправленной в Ассистента записи появляется в Jira")
    def test_entry_worklog_appears_in_jira(
        self,
        vinny_api: VinnyApi,
        jira_api: JiraApi,
        task_prefix: str,
        api_error_handler,
        task_number,
        time_spent,
        description,
    ):
        task = f"{task_prefix}-{task_number}"
        with api_error_handler():
            with allure.step(f"Создать запись в ассистенте для задачи {task}, точный текст записи, созданной в Ассистенте: '{description}'"):
                vinny_api.create_entry_for_today(
                    task=task,
                    time_spent=time_spent,
                    description=description,
                )
            with allure.step(f"Запросить последний worklog задачи {task} напрямую из Jira"):
                last_worklog = jira_api.get_last_worklog(task)
        with allure.step(f"Проверить что worklog для {task} существует в Jira"):
            assert last_worklog is not None
        with allure.step(f"Проверить что описание записи в Ассистенте == комментарию worklog в Jira: '{description}' in '{last_worklog.comment}'"):
            assert description in last_worklog.comment
        with allure.step(f"Проверить что время записи в Ассистенте == времени worklog в Jira: '{time_spent}' == '{last_worklog.timeSpent}'"):
            assert last_worklog.timeSpent == time_spent

    @pytest.mark.parametrize(
        "task_number, time_spent, description",
        [
            pytest.param(7, "", "1й негативный кейс, пустое время", id="empty_time_spent"),
            pytest.param(7, "15m", "", id="empty_description"),
        ],
    )
    @allure.title("Запись с невалидными данными не попадает в Jira")
    def test_invalid_entry_does_not_appear_in_jira(
        self,
        vinny_api: VinnyApi,
        jira_api: JiraApi,
        task_prefix: str,
        task_number,
        time_spent,
        description,
    ):
        task = f"{task_prefix}-{task_number}"
        with allure.step(f"Запомнить id последнего worklog задачи {task} до попытки создания записи"):
            worklog_before = jira_api.get_last_worklog(task)
        with allure.step(
            f"Создать запись в ассистенте для задачи {task} с невалидными данными "
            f"(time_spent='{time_spent}', description='{description}')"
        ):
            result = vinny_api.create_entry_for_today(
                task=task,
                time_spent=time_spent,
                description=description,
            )
        with allure.step(f"Проверить что ассистент вернул jira_status == 'error' (получено: '{result.jira_status}')"):
            assert result.jira_status == "error"
        with allure.step(f"Проверить что новый worklog не появился в Jira для {task}"):
            worklog_after = jira_api.get_last_worklog(task)
            id_before = worklog_before.id if worklog_before else None
            id_after = worklog_after.id if worklog_after else None
            assert id_after == id_before
