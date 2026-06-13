from utils.base_API import BaseApi
from utils.models.jira_models import JiraWorklogResponse, JiraWorklogItem


class JiraApi(BaseApi):

    def __init__(self, url: str, email: str, token: str):
        super().__init__(url)
        self.auth = (email, token)

    def get_worklogs(self, task_key: str) -> JiraWorklogResponse:
        response = self.get(
            endpoint=f"/rest/api/2/issue/{task_key}/worklog",
            model_type=JiraWorklogResponse,
            auth=self.auth,
        )
        return response.data

    def get_last_worklog(self, task_key: str) -> JiraWorklogItem | None:
        worklogs = self.get_worklogs(task_key).worklogs
        return worklogs[-1] if worklogs else None
