from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from nativedq.definitions import DQTest
from nativedq.execution.dq_execution_result import DQExecutionResult
from nativedq.execution.dq_test_result import DQTestResult

T = TypeVar('T')

class DQExecutionStrategy(ABC, Generic[T]):
    @abstractmethod
    def execute(self, df: T, tests:List[DQTest], resolve:bool=False) -> DQExecutionResult: raise NotImplementedError
    
    @abstractmethod
    def resolve(self, df: T, tests:List[DQTest]) -> List[DQTestResult]: raise NotImplementedError