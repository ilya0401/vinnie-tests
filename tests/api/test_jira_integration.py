from datetime import date, datetime, timedelta

import allure
import pytest
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi
from utils.kafka_ui_API import KafkaUiApi
from utils.wait import wait_until

JIRA_TOPIC = "jira-worklog-requests"
JIRA_CONSUMER_GROUP = "jira-delivery"

pytestmark = pytest.mark.usefixtures("drain_jira_delivery_queue")


@pytest.mark.jira_integration
class TestJiraWorklogDelivery:
    """Явно: проверяем факт доставки напрямую в Jira."""

    @pytest.mark.parametrize(
        "task_number, time_spent, description, days_ago",
        [
            pytest.param(1, "1h 45m", "тестовый дескрипшн, параметризация, позитивный кейс 1", 0, id="task_1"),
            pytest.param(1, "30m", "тестовый дескрипшн, параметризация, позитивный кейс 2", 0, id="task_1_second"),
            pytest.param(1, "1d", "тестовый дескрипшн, граница форматов: единица измерения сутки", 0, id="task_1_day_unit"),
            pytest.param(1, "1w", "тестовый дескрипшн, граница форматов: единица измерения неделя", 0, id="task_1_week_unit"),
            pytest.param(1, "0m", "тестовый дескрипшн, граница: минимальная продолжительность, принимаемая Jira", 0, id="task_1_zero_minutes"),
            pytest.param(1, "15m", "тестовый дескрипшн, дата записи — вчера, не сегодня", 1, id="task_1_yesterday"),
        ],
    )
    @allure.label("tc_id", "TC-011")
    @allure.title("[3.1.] Worklog отправленной в Ассистента записи появляется в Jira")
    def test_entry_worklog_appears_in_jira(
        self,
        vinny_api: VinnyApi,
        jira_api: JiraApi,
        kafka_ui_api: KafkaUiApi,
        task_prefix: str,
        api_error_handler,
        task_number,
        time_spent,
        description,
        days_ago,
    ):
        task = f"{task_prefix}-{task_number}"
        entry_date = (date.today() - timedelta(days=days_ago)).isoformat()
        with api_error_handler():
            with allure.step(f"Создать запись в ассистенте для задачи {task} на дату {entry_date}, точный текст записи, созданной в Ассистенте: '{description}'"):
                confirm_result = vinny_api.create_entry(
                    task=task,
                    entry_date=entry_date,
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
                f"поэтому дожидаемся появления worklog с описанием '{description}' у {task} (до 90с — "
                f"запас на случай ретраев консьюмера при кратковременных сетевых сбоях со стороны Jira)"
            ):
                def _matching_worklog():
                    worklog = jira_api.get_last_worklog(task)
                    return worklog if worklog and description in worklog.comment else None

                last_worklog = wait_until(_matching_worklog, timeout=90, interval=1)
        with allure.step(f"Проверить что worklog с описанием '{description}' появился в Jira для {task}"):
            assert last_worklog is not None
        with allure.step(f"Проверить что описание записи в Ассистенте == комментарию worklog в Jira: '{description}' in '{last_worklog.comment}'"):
            assert description in last_worklog.comment
        with allure.step(f"Проверить что время записи в Ассистенте == времени worklog в Jira: '{time_spent}' == '{last_worklog.timeSpent}'"):
            assert last_worklog.timeSpent == time_spent
        with allure.step(
            f"Проверить что дата worklog в Jira (started) == отправленной дате записи: "
            f"'{entry_date}' == '{last_worklog.started[:10] if last_worklog.started else None}'"
        ):
            assert last_worklog.started is not None
            assert last_worklog.started[:10] == entry_date
        with allure.step(
            f"Проверить что offset сообщения закоммичен (lag консьюмер-группы '{JIRA_CONSUMER_GROUP}' "
            f"по топику '{JIRA_TOPIC}' вернулся к 0)"
        ):
            kafka_ui_api.wait_for_zero_lag(topic=JIRA_TOPIC, group_id=JIRA_CONSUMER_GROUP, timeout=30)

    _INVALID_ENTRY_TC_IDS = {
        "empty_time_spent": "TC-015",
        "empty_description": "TC-013",
        "whitespace_only_description": "TC-014",
        "invalid_time_spent_format": "TC-015",
        "negative_time_spent": "TC-015",
    }

    @pytest.mark.parametrize(
        "task_number, time_spent, description",
        [
            pytest.param(1, "", "1й негативный кейс, пустое время", id="empty_time_spent"),
            pytest.param(1, "15m", "", id="empty_description"),
            pytest.param(1, "15m", "   ", id="whitespace_only_description"),
            pytest.param(1, "abc", "2й негативный кейс, нечисловой формат времени", id="invalid_time_spent_format"),
            pytest.param(1, "-5m", "3й негативный кейс, отрицательное время (граница с '0m' из TC-011)", id="negative_time_spent"),
        ],
    )
    @allure.title("Запись с невалидными данными не попадает в Jira")
    def test_invalid_entry_does_not_appear_in_jira(
        self,
        vinny_api: VinnyApi,
        jira_api: JiraApi,
        kafka_ui_api: KafkaUiApi,
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
            f"в мгновенном ответе: получено '{result.jira_status}'), поэтому дожидаемся обработки консьюмером "
            f"по факту коммита offset'а (lag консьюмер-группы '{JIRA_CONSUMER_GROUP}' по топику '{JIRA_TOPIC}' "
            "вернулся к 0), а не по фиксированной задержке"
        ):
            kafka_ui_api.wait_for_zero_lag(topic=JIRA_TOPIC, group_id=JIRA_CONSUMER_GROUP, timeout=90)
        with allure.step(f"Проверить что новый worklog не появился в Jira для {task}"):
            worklog_after = jira_api.get_last_worklog(task)
            id_before = worklog_before.id if worklog_before else None
            id_after = worklog_after.id if worklog_after else None
            assert id_after == id_before


@pytest.mark.jira_integration
class TestKafkaPublish:
    """Явно: проверяем факт и содержимое публикации в Kafka напрямую — не доставку в Jira."""

    @allure.label("tc_id", "TC-001")
    @allure.title("Опубликованное в Kafka сообщение совпадает с данными подтверждённой записи")
    def test_published_message_matches_confirmed_entry(
        self,
        vinny_api: VinnyApi,
        kafka_ui_api: KafkaUiApi,
        task_prefix: str,
        api_error_handler,
    ):
        task = f"{task_prefix}-1"
        time_spent = "20m"
        description = f"автотест: контент Kafka-сообщения [{datetime.now().isoformat()}]"
        with api_error_handler():
            with allure.step(f"Создать запись в ассистенте для задачи {task}: '{description}'"):
                result = vinny_api.create_entry_for_today(
                    task=task,
                    time_spent=time_spent,
                    description=description,
                )
        with allure.step(f"Прочитать последнее сообщение топика '{JIRA_TOPIC}' через kafka-ui"):
            message = kafka_ui_api.get_latest_message(JIRA_TOPIC)
        with allure.step(
            f"Проверить что сообщение в Kafka соответствует подтверждённой записи "
            f"(entry_id={result.id}, task='{task}', time_spent='{time_spent}')"
        ):
            assert message is not None, f"Топик '{JIRA_TOPIC}' пуст"
            assert message["entry_id"] == result.id
            assert message["task"] == task
            assert message["time_spent"] == time_spent
            assert message["description"] == description
        with allure.step(
            f"Проверить что запись entry_id={result.id} не попала в другие топики кластера "
            f"(кроме '{JIRA_TOPIC}')"
        ):
            kafka_ui_api.assert_entry_absent_from_other_topics(entry_id=result.id, exclude_topic=JIRA_TOPIC)
