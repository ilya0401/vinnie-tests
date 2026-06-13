from typing import Optional
from pydantic import BaseModel


class JiraWorklogAuthor(BaseModel):
    emailAddress: Optional[str] = None
    displayName: Optional[str] = None


class JiraWorklogItem(BaseModel):
    id: Optional[str] = None
    comment: Optional[str] = None
    timeSpent: Optional[str] = None
    timeSpentSeconds: Optional[int] = None
    author: Optional[JiraWorklogAuthor] = None
    started: Optional[str] = None


class JiraWorklogResponse(BaseModel):
    total: int
    worklogs: list[JiraWorklogItem]