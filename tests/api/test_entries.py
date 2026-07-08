import allure
import pytest
from utils.vinny_API import VinnyApi
from utils import decorators


@pytest.mark.entries
class TestEntries:


    @allure.title("[1.1.] Отправляем запрос к ассистенту GET /entries: проверка доступности Ассистента")
    @decorators.time_measure
    def test_entries_returns_list(self, vinny_api: VinnyApi, api_error_handler):
        with api_error_handler():
            with allure.step("Запросить все записи у ассистента"):
                entries = vinny_api.get_all_entries()
        with allure.step("Убеждаемся что эндпоинт живой и отвечает корректно"):
            assert isinstance(entries, list)

    @allure.title("[1.2.] Создание записи в ассистенте возвращает статус success")
    @decorators.time_measure
    def test_create_entry_returns_success_status(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        with api_error_handler():
            with allure.step("Создать запись на сегодня"):
                result = vinny_api.create_entry_for_today(
                    task=test_task,
                    time_spent="15m",
                    description="автотест: проверка создания записи",
                )
        with allure.step("Проверить что status создания записи == success"):
            assert result.status == "success"

    @allure.title("[1.3.] Данные созданной записи в Ассистенте совпадают с отправленными в него")
    def test_created_entry_data_matches_sent_data(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        description = "автотест: проверка данных записи"
        with api_error_handler():
            with allure.step(f"Создать запись для задачи {test_task} с описанием '{description}'"):
                result = vinny_api.create_entry_for_today(
                    task=test_task,
                    time_spent="1h",
                    description=description,
                )
            with allure.step(f"Запросить у ассистента запись по id={result.id}"):
                entry = vinny_api.get_entry_by_id(result.id)
        with allure.step(f"Проверить task: отправлено '{test_task}' == получено '{entry.task}'"):
            assert entry.task == test_task
        with allure.step(f"Проверить description: отправлено '{description}' == получено '{entry.description}'"):
            assert entry.description == description
