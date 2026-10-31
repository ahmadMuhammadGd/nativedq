from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

from nativedq.definitions.dq_test import DQTest
from nativedq.execution.dq_execution_result import DQExecutionResult

T = TypeVar('T')


class DQExecutorConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

class DQExecutor(ABC, Generic[T]):

    @abstractmethod
    def run(self, df: Optional[T], tests: List[DQTest], resolve:bool=False) -> DQExecutionResult[T]: 
        raise NotImplementedError