from typing import Optional
from pydantic import BaseModel


class ConsumerGroupInfo(BaseModel):
    groupId: str
    state: Optional[str] = None
    consumerLag: Optional[int] = None
