import os
import sys

import pytest

# Spark launches Python worker processes from PATH.  If that interpreter is a
# different minor version than the driver, Spark refuses to run the job (in this
# environment ``python`` on PATH is 3.14 while the project venv is 3.12), so
# point the workers at the interpreter running the tests.
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

from dqt.definitions import DQTest
from pyspark.sql import SparkSession

SCHEMA = "id int, value int, category string"

# ``value`` contains a NULL and a negative number, so failure and NULL handling
# can both be exercised on the same frame.
ROWS = [
    (1, 10, "a"),
    (2, 20, "b"),
    (3, None, "c"),
    (4, -5, None),
]


class ThresholdDQTest(DQTest):
    """A DQTest whose invocation always carries the same error threshold.

    The strategies call ``test()`` without arguments, so a threshold has to be
    carried by the definition itself to be observable.
    """

    threshold: float = 100.0

    def __call__(self, *args, maximum_accepted_error_percentage=None, **kwargs):
        if maximum_accepted_error_percentage is None:
            maximum_accepted_error_percentage = self.threshold
        return super().__call__(
            *args,
            maximum_accepted_error_percentage=maximum_accepted_error_percentage,
            **kwargs,
        )


@pytest.fixture(scope="session")
def spark():
    """Run a single local Spark session for the whole test session."""
    session = (
        SparkSession.builder.master("local[1]")
        .appName("dqt-spark35-executor-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .getOrCreate()
    )
    session.sparkContext.setLogLevel("ERROR")
    try:
        yield session
    finally:
        session.stop()


@pytest.fixture
def make_dataframe(spark):
    """Return a factory building small real DataFrames."""

    def factory(rows=None, schema=SCHEMA):
        return spark.createDataFrame(ROWS if rows is None else rows, schema)

    return factory


@pytest.fixture
def df(make_dataframe):
    """A four-row frame with a NULL and a negative value in ``value``."""
    return make_dataframe()


@pytest.fixture
def make_test():
    """Return a factory creating DQTest definitions from rule functions."""

    def factory(func, name=None, threshold=None):
        kwargs = {"func": func}
        if name is not None:
            kwargs["name"] = name
        if threshold is None:
            return DQTest(**kwargs)
        return ThresholdDQTest(**kwargs, threshold=threshold)

    return factory


@pytest.fixture
def column_values():
    """Return a reader for the values of one column, in row order."""

    def read(frame, name):
        return [row[name] for row in frame.select(name).orderBy("id").collect()]

    return read
