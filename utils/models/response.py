from dataclasses import dataclass
from typing import Optional, Iterable

from requests import Response as ApiResponse

@dataclass
class ResponseSchema[T]:
    raw: ApiResponse
    data: Optional[T | Iterable[T]]
