import time

import allure
import pytest
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi
from utils.wait import wait_until


@pytest.mark.jira_integration
class TestJiraWorklogDelivery:
    """Явно: проверяем факт доставки напрямую в Jira."""

    @pytest.mark.parametrize(
        "task_number, time_spent, description",
        [
            pytest.param(1, "1h 45m", "тестовый дескрипшн, параметризация, позитивный кейс 1", id="task_1"),
            pytest.param(1, "30m", "тестовый дескрипшн, параметризация, позитивный кейс 2", id="task_1_second"),
        ],
    )
    @allure.label("tc_id", "TC-011")
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
                confirm_result = vinny_api.create_entry_for_today(
                    task=task,
                    time_spent=time_spent,
                    description=description,
                )
            with allure.step(
                f"Проверить что Ассистент поставил запись в очередь на доставку в Jira (jira_status='queued'), "
                f"получено: '{confirm_result.jira_status}'"
            ):
                assert confirm_result.jira_status == "queued"
            with allure.step(
                f"Ассистент отправляет worklog в Jira асинхронно (через Kafka-очередь и консьюмер), "
                f"поэтому дожидаемся появления worklog с описанием '{description}' у {task} (до 30с)"
            ):
                def _matching_worklog():
                    worklog = jira_api.get_last_worklog(task)
                    return worklog if worklog and description in worklog.comment else None

                last_worklog = wait_until(_matching_worklog, timeout=30, interval=1)
        with allure.step(f"Проверить что worklog с описанием '{description}' появился в Jira для {task}"):
            assert last_worklog is not None
        with allure.step(f"Проверить что описание записи в Ассистенте == комментарию worklog в Jira: '{description}' in '{last_worklog.comment}'"):
            assert description in last_worklog.comment
        with allure.step(f"Проверить что время записи в Ассистенте == времени worklog в Jira: '{time_spent}' == '{last_worklog.timeSpent}'"):
            assert last_worklog.timeSpent == time_spent

    _INVALID_ENTRY_TC_IDS = {
        "empty_time_spent": "TC-015",
        "empty_description": "TC-013",
        "whitespace_only_description": "TC-014",
    }

    @pytest.mark.parametrize(
        "task_number, time_spent, description",
        [
            pytest.param(1, "", "1й негативный кейс, пустое время", id="empty_time_spent"),
            pytest.param(1, "15m", "", id="empty_description"),
            pytest.param(1, "15m", "   ", id="whitespace_only_description"),
        ],
    )
    @allure.title("Запись с невалидными данными не попадает в Jira")
    def test_invalid_entry_does_not_appear_in_jira(
        self,
        vinny_api: VinnyApi,
        jira_api: JiraApi,
        task_prefix: str,
        request,
        task_number,
        time_spent,
        description,
    ):
        allure.dynamic.label("tc_id", self._INVALID_ENTRY_TC_IDS[request.node.callspec.id])
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
        with allure.step(
            "Ассистент принимает запись в очередь независимо от валидности (jira_status всегда 'queued' "
            f"в мгновенном ответе: получено '{result.jira_status}'), поэтому ждём окно обработки консьюмером "
            "и проверяем результат напрямую в Jira, а не мгновенный ответ"
        ):
            time.sleep(15)
        with allure.step(f"Проверить что новый worklog не появился в Jira для {task}"):
            worklog_after = jira_api.get_last_worklog(task)
            id_before = worklog_before.id if worklog_before else None
            id_after = worklog_after.id if worklog_after else None
            assert id_after == id_before
