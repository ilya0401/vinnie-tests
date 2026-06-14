import allure
from utils.vinny_API import VinnyApi


class TestEntries:

    @allure.title("Отправляем запрос к ассистенту GET /entries: проверка доступности Ассистента")
    def test_entries_returns_list(self, vinny_api: VinnyApi):
        with allure.step("Запросить все записи у ассистента"):
            entries = vinny_api.get_all_entries()
        with allure.step("Убеждаемся что эндпоинт живой и отвечает корректно"):
            assert isinstance(entries, list)

    @allure.title("Создание записи в ассистенте возвращает статус success")
    def test_create_entry_returns_success_status(self, vinny_api: VinnyApi, test_task: str):
        with allure.step("Создать запись на сегодня"):
            result = vinny_api.create_entry_for_today(
                task=test_task,
                time_spent="15m",
                description="автотест: проверка создания записи",
            )
        with allure.step("Проверить что status создания записи == success"):
            assert result.status == "success"

    @allure.title("Данные созданной записи в Ассистенте совпадают с отправленными в него")
    def test_created_entry_data_matches_sent_data(self, vinny_api: VinnyApi, test_task: str):
        description = "автотест: проверка данных записи"
        with allure.step("Создать запись на сегодня"):
            result = vinny_api.create_entry_for_today(
                task=test_task,
                time_spent="1h",
                description=description,
            )
        with allure.step("Запросить у ассистента запись по id"):
            entry = vinny_api.get_entry_by_id(result.id)
        with allure.step("Проверить что task и description положенные в Ассистента совпадают с отправленными"):
            assert entry.task == test_task
            assert entry.description == description