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

    @pytest.mark.parametrize(
        "bad_date",
        [
            pytest.param("2026/07/14", id="slash_format"),
            pytest.param("20260714", id="compact_iso_no_dashes"),
            pytest.param("2026-W29-2", id="iso_week_date"),
            pytest.param("14-07-2026", id="dd_mm_yyyy_dashes"),
        ],
    )
    @allure.label("bug_id", "KAN-4")
    @allure.title("[1.4.] Создание записи с невалидным форматом даты возвращает статус error")
    def test_create_entry_with_invalid_date_returns_error_status(
        self, vinny_api: VinnyApi, test_task: str, api_error_handler, bad_date
    ):
        with api_error_handler():
            with allure.step(f"Создать запись с невалидным форматом даты '{bad_date}'"):
                result = vinny_api.create_entry(
                    task=test_task,
                    entry_date=bad_date,
                    time_spent="15m",
                    description="автотест: невалидный формат даты",
                )
        with allure.step(f"Проверить что status == error для даты '{bad_date}'"):
            assert result.status == "error"

    @allure.title("[1.3.] Данные созданной записи в Ассистенте совпадают с отправленными в него")
    def test_created_entry_data_matches_sent_data(self, vinny_api: VinnyApi, test_task: str, api_error_handler):
        description = "автотест: проверка данных записи"
        time_spent = "1h"
        with api_error_handler():
            with allure.step(f"Создать запись для задачи {test_task} с описанием '{description}'"):
                result = vinny_api.create_entry_for_today(
                    task=test_task,
                    time_spent=time_spent,
                    description=description,
                )
            with allure.step(f"Запросить у ассистента запись по id={result.id}"):
                entry = vinny_api.get_entry_by_id(result.id)
        with allure.step(f"Проверить task: отправлено '{test_task}' == получено '{entry.task}'"):
            assert entry.task == test_task
        with allure.step(f"Проверить description: отправлено '{description}' == получено '{entry.description}'"):
            assert entry.description == description
        with allure.step(f"Проверить time_spent: отправлено '{time_spent}' == получено '{entry.time_spent}'"):
            assert entry.time_spent == time_spent

    @pytest.mark.parametrize(
        "nonexistent_id",
        [
            pytest.param(999999999, id="far_above_any_real_id"),
            pytest.param(0, id="zero"),
            pytest.param(-1, id="negative"),
        ],
    )
    @allure.title("[1.5.] Запрос записи по не существующему id возвращает 404")
    def test_get_entry_by_nonexistent_id_returns_none(self, vinny_api: VinnyApi, nonexistent_id):
        with allure.step(f"Запросить у ассистента запись по заведомо не существующему id={nonexistent_id}"):
            entry = vinny_api.get_entry_by_id(nonexistent_id)
        with allure.step(f"Проверить что GET /entries/{nonexistent_id} вернул 404 (None)"):
            assert entry is None
