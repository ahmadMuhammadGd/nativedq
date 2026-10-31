from typing import Callable

from nativedq.definitions import DQTest


def dq_test(
    name: str | Callable | None = None,
    description: str | None = None,
    target_engine: str | None = None
):
    if callable(name):
        return DQTest(func=name)

    def _inner(fn: Callable):
        return DQTest(
            func=fn,
            name=name,
            description=description,
            target_engine=target_engine
        )

    return _inner