from typing import Any, Callable, List

from pydantic import BaseModel, model_validator


class DQTestCallParameter(BaseModel):
    name: str
    value: Any

class DQTestCall(BaseModel):
    func_callable: Callable
    parameters: List[DQTestCallParameter]
    maximum_accepted_error_percentage: float | None = 100
    
    @model_validator(mode="after")
    def validate(self):
        self.maximum_accepted_error_percentage = (
            100 
            if self.maximum_accepted_error_percentage is None
            else self.maximum_accepted_error_percentage
        )
        
        return self