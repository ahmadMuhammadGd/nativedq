from typing import Literal

from dqt.definitions import DQTest
from pydantic import BaseModel


class DQTestResult(BaseModel):
    test: DQTest
    status: Literal["PASS", "FAILED"]
    failed_percentage: float
    failed_rows: int | None = None
    evaluated_rows: int | None = None
