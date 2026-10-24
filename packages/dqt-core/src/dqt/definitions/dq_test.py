from inspect import Parameter, signature
from typing import Any, Callable

from dqt.models import (
    DQTestCall,
    DQTestCallParameter,
    DQTestParameter,
)
from pydantic import BaseModel, computed_field, model_validator


class DQTest(BaseModel):
    func: Callable

    name: str | None = None
    description: str | None = None
    target_engine: str | None = None

    def _handle_test_name(self) -> str:
        return self.name or self.func.__name__

    def _handle_test_description(self) -> str | None:
        return self.description or self.func.__doc__

    @computed_field
    @property
    def test_parameters(self) -> list[DQTestParameter]:
        return [
            DQTestParameter(
                name=name,
                annotation=param.annotation,
                default=(
                    None
                    if param.default is Parameter.empty
                    else param.default
                ),
            )
            for name, param in signature(self.func).parameters.items()
        ]

    @model_validator(mode="after")
    def validate(self) -> "DQTest":
        self.name = self._handle_test_name()
        self.description = self._handle_test_description()
        return self

    def __call__(
        self,
        *args: Any,
        maximum_accepted_error_percentage: float | None = None,
        **kwargs: Any,
    ) -> DQTestCall:
        bound = signature(self.func).bind(*args, **kwargs)
        bound.apply_defaults()

        return DQTestCall(
            func_callable=self.func,
            parameters=[
                DQTestCallParameter(name=name, value=value)
                for name, value in bound.arguments.items()
            ],
            maximum_accepted_error_percentage=maximum_accepted_error_percentage,
        )