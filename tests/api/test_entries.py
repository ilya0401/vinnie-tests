from utils.vinny_API import VinnyApi


class TestEntries:

    def test_entries_returns_list(self, vinny_api: VinnyApi):
        entries = vinny_api.get_all_entries()
        assert isinstance(entries, list)

    def test_create_entry_returns_success_status(self, vinny_api: VinnyApi, test_task: str):
        result = vinny_api.create_entry_for_today(
            task=test_task,
            time_spent="15m",
            description="автотест: проверка создания записи",
        )
        assert result.status == "success"



    def test_created_entry_data_matches_sent_data(self, vinny_api: VinnyApi, test_task: str):
        description = "автотест: проверка данных записи"
        result = vinny_api.create_entry_for_today(
            task=test_task,
            time_spent="1h",
            description=description,
        )
        entry = vinny_api.get_entry_by_id(result.id)
        assert entry.task == test_task
        assert entry.description == description
