import os
import pytest
import requests
from contextlib import contextmanager
from dotenv import load_dotenv
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi
from utils.kafka_ui_API import KafkaUiApi

load_dotenv(".env.test")


_HTTP_ERROR_MESSAGES = {
    400: "Некорректный запрос (400 Bad Request)",
    403: "Ошибка авторизации (403 Forbidden) — возможно протух токен Jira",
    404: "Ресурс не найден (404 Not Found)",
    422: "Ошибка валидации запроса (422 Unprocessable Entity)",
    500: "Внутренняя ошибка ассистента (500 Internal Server Error)",
    503: "Ассистент перегружен или не готов (503 Service Unavailable)",
}


@pytest.fixture
def api_error_handler():
    @contextmanager
    def handle():
        try:
            yield
        except requests.exceptions.ConnectionError:
            pytest.fail("Ассистент недоступен: не удалось установить соединение (контейнер выключен?)")
        except requests.exceptions.Timeout:
            pytest.fail("Ассистент не отвечает: превышено время ожидания")
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code
            msg = _HTTP_ERROR_MESSAGES.get(status, f"HTTP ошибка: {status}")
            pytest.fail(msg)

    return handle


@pytest.fixture(scope="session")
def vinny_api() -> VinnyApi:
    return VinnyApi(os.getenv("VINNY_URL", "http://localhost:8000"))


@pytest.fixture(scope="session")
def test_task() -> str:
    return os.getenv("JIRA_TEST_TASK", "KAN-9")


@pytest.fixture(scope="session")
def task_prefix() -> str:
    return os.getenv("TASK_PREFIX", "KAN")


@pytest.fixture(scope="session")
def jira_api() -> JiraApi:
    return JiraApi(
        url=os.getenv("JIRA_URL", "https://iyk040190.atlassian.net"),
        email=os.getenv("JIRA_EMAIL", "iyk040190@gmail.com"),
        token=os.getenv("JIRA_API_TOKEN", ""),
    )


@pytest.fixture(scope="session")
def kafka_ui_api() -> KafkaUiApi:
    return KafkaUiApi(
        url=os.getenv("KAFKA_UI_URL", "http://localhost:8090"),
        cluster="vinnie",
    )


@pytest.fixture
def drain_jira_delivery_queue(kafka_ui_api: KafkaUiApi):
    """Дожидается lag=0 консьюмер-группы 'jira-delivery' по топику 'jira-worklog-requests'
    ПЕРЕД тестом, а не только после него. Если предыдущий тест не дождался своего воркалога
    и упал по assert, он не доходит до собственного финального wait_for_zero_lag — опоздавшее
    сообщение остаётся в очереди и может долетать уже во время следующего теста, давая ложный
    результат там, где реального дефекта нет. Используется через module-level pytestmark в
    test_jira_integration.py / test_jira_sync.py, не глобально — не нужна тестам, не трогающим
    эту очередь."""
    kafka_ui_api.wait_for_zero_lag(topic="jira-worklog-requests", group_id="jira-delivery", timeout=90)
