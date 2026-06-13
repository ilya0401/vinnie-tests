import os
import pytest
from dotenv import load_dotenv
from utils.vinny_API import VinnyApi
from utils.jira_API import JiraApi

load_dotenv(".env.test")


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
