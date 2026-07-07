from datetime import date
from utils.base_API import BaseApi, APIMethods
from utils.models.vinny_models import ConfirmResponseSchema, EntrySchema, JiraTestResponseSchema


class VinnyApi(BaseApi):

    class Endpoints:
        CONFIRM = "/confirm"
        ENTRIES = "/entries"
        PROCESS = "/process"
        JIRA_TEST = "/jira-test"

    def __init__(self, url: str):
        super().__init__(url)

    def create_entry(
        self,
        task: str,
        entry_date: str,
        time_spent: str,
        description: str,
        transcribed: str = "",
    ) -> ConfirmResponseSchema:
        response = self.send(
            APIMethods.POST,
            endpoint=self.Endpoints.CONFIRM,
            json={
                "task": task,
                "date": entry_date,
                "time_spent": time_spent,
                "description": description,
                "transcribed": transcribed,
            },
            model_type=ConfirmResponseSchema,
        )
        return response.data

    def create_entry_for_today(
        self,
        task: str,
        time_spent: str,
        description: str,
    ) -> ConfirmResponseSchema:
        return self.create_entry(
            task=task,
            entry_date=date.today().isoformat(),
            time_spent=time_spent,
            description=description,
        )

    def get_all_entries(self) -> list[EntrySchema]:
        response = self.get(
            endpoint=self.Endpoints.ENTRIES,
            model_type=list[EntrySchema],
        )
        return response.data

    def get_entry_by_id(self, entry_id: int) -> EntrySchema | None:
        import requests
        try:
            response = self.get(
                endpoint=f"{self.Endpoints.ENTRIES}/{entry_id}",
                model_type=EntrySchema,
            )
            return response.data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise

    def check_jira_connection(self, task_key: str) -> JiraTestResponseSchema:
        response = self.get(
            endpoint=f"{self.Endpoints.JIRA_TEST}/{task_key}",
            model_type=JiraTestResponseSchema,
        )
        return response.data
