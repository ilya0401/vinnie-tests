from typing import Optional
from pydantic import BaseModel


class EntrySchema(BaseModel):
    id: Optional[int] = None
    task: Optional[str] = None
    date: Optional[str] = None
    time_spent: Optional[str] = None
    description: Optional[str] = None
    added: Optional[str] = None


class ParsedEntrySchema(BaseModel):
    task: Optional[str] = None
    date: Optional[str] = None
    time_spent: Optional[str] = None
    description: Optional[str] = None


class ConfirmResponseSchema(BaseModel):
    status: str
    voice_message: str
    jira_status: str
    id: int
    transcribed: Optional[str] = None
    parsed: Optional[ParsedEntrySchema] = None


class JiraTestResponseSchema(BaseModel):
    configured: bool
    url: Optional[str] = None
    status: Optional[int] = None
    email: Optional[str] = None
    body_preview: Optional[str] = None
    error: Optional[str] = None