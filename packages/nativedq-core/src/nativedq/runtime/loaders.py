
from importlib.metadata import entry_points
from typing import Any

from nativedq.abc.dq_execute import DQExecutor, DQExecutorConfig

EXECUTOR_ENTRY_POINT_GROUP = "nativedq.executors"

def discover_executors() -> dict[str, type]:
    """Discover installed executor plugins."""
    discovered = entry_points().select(group=EXECUTOR_ENTRY_POINT_GROUP)

    executors = {}

    for entry_point in discovered:
        if entry_point.name in executors:
            raise ValueError(
                f"Duplicate executor registration: {entry_point.name!r}"
            )

        executors[entry_point.name] = entry_point.load()

    return executors


def load_executor(name: str, config: DQExecutorConfig) -> DQExecutor:
    """Load and instantiate a registered executor."""
    executors = discover_executors()

    executor_cls = executors.get(name)

    if executor_cls is None:
        available = sorted(executors)
        raise ValueError(
            f"Unknown executor {name!r}. "
            f"Available executors: {available}"
        )

    return executor_cls(config)
