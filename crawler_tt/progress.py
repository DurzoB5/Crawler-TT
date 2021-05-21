import json
import logging
import os
from enum import Enum
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger('crawler')


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

    @property
    def json(self) -> Dict[str, Any]:
        return {'state': self.state.value, 'error': self.error, 'finding': self.finding}


class BaseProgressHandler:
    def __init__(self, result: str):
        self.result = result
        self.results: Dict[str, Any] = {}

    @property
    def urls(self) -> List[str]:
        raise NotImplementedError()

    def store_result(self, url: str, result: Result) -> None:
        raise NotImplementedError()


class StandaloneProgressHandler(BaseProgressHandler):
    def __init__(self, result: str):
        super().__init__(result)

        if os.path.exists(result):
            LOGGER.info(f'Loading results from pre-existing results at {result}')
            with open(result, 'r') as result_file:
                data = json.load(result_file)

                for url, results in data.items():
                    results['state'] = State(results['state'])
                    self.results[url] = Result(**results)

    @property
    def urls(self) -> List[str]:
        return list(self.results.keys())

    def store_result(self, url: str, result: Result) -> None:
        self.results[url] = result

        with open(self.result, 'w') as result_file:
            output = {}

            for url, result in self.results.items():
                output[url] = result.json

            json.dump(output, result_file)


class ServiceProgressHandler(BaseProgressHandler):
    pass
