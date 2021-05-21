from enum import Enum
from typing import List, Optional


class State(Enum):
    SAFE = 'safe'
    FAILURE = 'failure'
    VULNERABLE = 'vulnerable'


class Result:
    """A class that handles the result of SQL injections for a given url"""

    def __init__(
        self,
        state: State,
        finding: Optional[str] = None,
        error: Optional[str] = None,
    ):
        self.state = state
        self.error = error
        self.finding = finding


class BaseProgressHandler:
    def __init__(self, result: str):
        raise NotImplementedError()

    @property
    def urls(self) -> List[str]:
        raise NotImplementedError()

    def store_result(self, url: str, result: Result) -> None:
        raise NotImplementedError()


class StandaloneProgressHandler(BaseProgressHandler):
    def __init__(self, result: str):
        self.result_file = result
        self.results = {}

    @property
    def urls(self) -> List[str]:
        return list(self.results.keys())

    def store_result(self, url: str, result: Result) -> None:
        self.results[url] = result


class ServiceProgressHandler(BaseProgressHandler):
    pass
