import time
from typing import Callable, TypeVar

T = TypeVar("T")


def wait_until(predicate: Callable[[], T], timeout: float = 15, interval: float = 1) -> T | None:
    deadline = time.monotonic() + timeout
    result = predicate()
    while not result and time.monotonic() < deadline:
        time.sleep(interval)
        result = predicate()
    return result
