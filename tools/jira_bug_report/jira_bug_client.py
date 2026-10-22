import hashlib
import os

import requests


class JiraBugClient:
    """Тонкий клиент над Jira REST API v2 для автосоздания багов из результатов прогона тестов.

    Используется v2, а не v3: v2 принимает description/comment как обычную строку,
    v3 требует Atlassian Document Format (ADF) для тех же полей — а весь остальной
    проект (utils/jira_API.py) уже построен на v2, нет смысла заводить второй формат.
    """

    def __init__(self, url: str, email: str, token: str, project_key: str):
        self.url = url.rstrip("/")
        self.auth = (email, token)
        self.project_key = project_key
        self._issue_type_id: str | None = None

    @classmethod
    def from_env(cls) -> "JiraBugClient":
        url = os.getenv("JIRA_URL")
        token = os.getenv("JIRA_API_TOKEN")
        if not url or not token:
            raise RuntimeError(
                "Нужны переменные окружения JIRA_URL и JIRA_API_TOKEN (например, в .env.test)"
            )
        return cls(
            url=url,
            email=os.getenv("JIRA_EMAIL", "iyk040190@gmail.com"),
            token=token,
            project_key=os.getenv("TASK_PREFIX", "KAN"),
        )

    @staticmethod
    def make_fingerprint(seed: str) -> str:
        """Стабильный короткий хэш identity бага — не меняется между прогонами,
        чтобы повторные обнаружения того же дефекта не плодили дубликаты тикетов."""
        return hashlib.sha256(seed.strip().lower().encode("utf-8")).hexdigest()[:12]

    def _bug_issue_type_id(self) -> str:
        if self._issue_type_id:
            return self._issue_type_id
        response = requests.get(
            f"{self.url}/rest/api/2/project/{self.project_key}",
            auth=self.auth,
            timeout=10,
        )
        response.raise_for_status()
        issue_types = response.json().get("issueTypes", [])
        for candidate_name in ("Bug", "Баг"):
            for issue_type in issue_types:
                if issue_type["name"] == candidate_name and not issue_type.get("subtask"):
                    self._issue_type_id = issue_type["id"]
                    return self._issue_type_id
        available = ", ".join(it["name"] for it in issue_types)
        raise RuntimeError(
            f"В проекте {self.project_key} не нашёл тип задачи 'Bug'/'Баг'. Доступные типы: {available}"
        )

    def find_existing(self, fingerprint: str) -> dict | None:
        """Ищет уже существующий тикет с тем же fingerprint (любой статус) — чтобы не плодить дубликаты
        на повторные обнаружения одного и того же дефекта в последующих прогонах.

        /rest/api/2/search и /rest/api/3/search удалены Atlassian (410 Gone) —
        актуальный поиск только через /rest/api/3/search/jql."""
        jql = f'project = "{self.project_key}" AND summary ~ "fp:{fingerprint}"'
        response = requests.get(
            f"{self.url}/rest/api/3/search/jql",
            auth=self.auth,
            params={"jql": jql, "fields": "summary,status"},
            timeout=10,
        )
        response.raise_for_status()
        issues = response.json().get("issues", [])
        return issues[0] if issues else None

    def create_bug(
        self,
        title: str,
        description: str,
        fingerprint: str,
        severity: str,
        labels: list[str] | None = None,
    ) -> dict:
        full_summary = f"{title} [fp:{fingerprint}]"
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "issuetype": {"id": self._bug_issue_type_id()},
                "summary": full_summary,
                "description": description,
                "labels": ["autobug", f"severity-{severity}", *(labels or [])],
            }
        }
        response = requests.post(
            f"{self.url}/rest/api/2/issue",
            auth=self.auth,
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def add_comment(self, issue_key: str, text: str) -> dict:
        response = requests.post(
            f"{self.url}/rest/api/2/issue/{issue_key}/comment",
            auth=self.auth,
            json={"body": text},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()

    def issue_url(self, issue_key: str) -> str:
        return f"{self.url}/browse/{issue_key}"
