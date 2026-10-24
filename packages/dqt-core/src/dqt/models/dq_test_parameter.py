from typing import Any

from pydantic import BaseModel


class DQTestParameter(BaseModel):
    name: str
    annotation: Any
    default: Any