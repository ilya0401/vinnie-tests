from utils.vinny_API import VinnyApi


class TestJiraSync:

    def test_jira_connection_is_configured_and_reachable(self, vinny_api: VinnyApi, test_task: str):
        result = vinny_api.check_jira_connection(test_task)
        assert result.configured is True
        assert result.status == 200

    def test_create_entry_logs_to_jira(self, vinny_api: VinnyApi, test_task: str):
        result = vinny_api.create_entry_for_today(
            task=test_task,
            time_spent="15m",
            description="автотест: проверка логирования в Jira",
        )
        assert result.jira_status == "ok"

    def test_nonexistent_task_returns_not_found(self, vinny_api: VinnyApi):
        result = vinny_api.create_entry_for_today(
            task="KAN-99999",
            time_spent="15m",
            description="автотест: несуществующая задача",
        )
        assert result.jira_status == "not_found"
