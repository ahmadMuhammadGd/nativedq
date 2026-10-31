from functools import partial

import pytest
from nativedq.definitions import DQTest
from nativedq_spark35_executor.strategies.helpers.get_exprs import get_expr, get_exprs
from pyspark.sql import Column
from pyspark.sql import functions as F


def _rule(column: str = "value", limit: int = 10):
    return f"{column} < {limit}"


def _positive(column: str = "value"):
    return F.col(column) > 0


def test_builds_expression_with_default_parameters():
    assert get_expr(DQTest(func=_rule)) == "value < 10"


def test_builds_expression_with_partial_parameters():
    test = DQTest(func=partial(_rule, column="age"), name="age_rule")

    assert get_expr(test) == "age < 10"


def test_builds_a_spark_column_expression(spark):
    expression = get_expr(DQTest(func=_positive))

    assert isinstance(expression, Column)


def test_evaluates_the_expression_against_real_rows(spark, df):
    expression = get_expr(DQTest(func=_positive))

    values = [row["ok"] for row in df.select(expression.alias("ok")).collect()]

    # NULL rows evaluate to NULL rather than to False.
    assert values == [True, True, None, False]


def test_builds_one_expression_per_test_in_order(spark, df):
    def first(column: str = "id"):
        return F.col(column) < 3

    def second(column: str = "id"):
        return F.col(column) < 2

    expressions = get_exprs([DQTest(func=first), DQTest(func=second)])

    assert len(expressions) == 2
    frame = df.select(
        expressions[0].alias("first"),
        expressions[1].alias("second"),
    )
    assert [(row["first"], row["second"]) for row in frame.collect()] == [
        (True, True),
        (True, False),
        (False, False),
        (False, False),
    ]


def test_returns_no_expressions_for_no_tests():
    assert get_exprs([]) == []


def test_propagates_missing_parameter_errors():
    def needs_parameter(value):
        return value

    with pytest.raises(TypeError):
        get_expr(DQTest(func=needs_parameter))
