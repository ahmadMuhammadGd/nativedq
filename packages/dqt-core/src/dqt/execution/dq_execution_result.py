from typing import Any, Dict, Generic, List, TypeVar
from uuid import uuid4

from dqt.execution.dq_test_result import DQTestResult
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar('T')

class DQExecutionResult(BaseModel, Generic[T]):
    uuid: str = Field(default_factory=lambda : uuid4().__str__())
    test_results: List[DQTestResult]
    result_df: T
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)