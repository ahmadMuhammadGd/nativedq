import pytest
from dqt.execution import DQExecutionResult
from dqt_spark35_executor.strategies import DirectResolveStrategy
from pyspark.sql import functions as F


def _positive(column: str = "value"):
    return F.col(column) > 0


def _not_null(column: str = "value"):
    return F.col(column).isNotNull()


def _small_id(column: str = "id"):
    return F.col(column) < 2


def test_execute_rejects_resolve_false(df, make_test):
    with pytest.raises(ValueError, match="resolve=True"):
        DirectResolveStrategy().execute(df, [make_test(_positive)], resolve=False)


def test_execute_returns_results_with_metadata(df, make_test):
    tests = [make_test(_positive), make_test(_not_null, name="not_null")]

    result = DirectResolveStrategy().execute(df, tests)

    assert isinstance(result, DQExecutionResult)
    assert result.result_df is df
    # Unnamed tests fall back to the rule function's name.
    assert result.metadata == {"test_indexes": {0: "_positive", 1: "not_null"}}
    assert [item.test for item in result.test_results] == tests
    assert [item.status for item in result.test_results] == ["PASS", "PASS"]


def test_execute_keeps_the_input_frame_intact(df, make_test):
    result = DirectResolveStrategy().execute(df, [make_test(_positive)])

    assert result.result_df.columns == ["id", "value", "category"]
    assert result.result_df.count() == df.count()


def test_resolve_computes_the_failure_ratio_of_each_rule(df, make_test):
    results = DirectResolveStrategy().resolve(
        df,
        [make_test(_positive), make_test(_not_null), make_test(_small_id)],
    )

    assert [item.test.name for item in results] == [
        "_positive",
        "_not_null",
        "_small_id",
    ]
    # value is 10, 20, NULL, -5; id is 1, 2, 3, 4.
    assert [item.failed_percentage for item in results] == [
        pytest.approx(50.0),
        pytest.approx(25.0),
        pytest.approx(75.0),
    ]
    assert [item.status for item in results] == ["PASS", "PASS", "PASS"]


def test_resolve_counts_null_results_as_failures(df, make_test):
    # Only the row whose ``value`` is NULL violates the not-null rule.
    results = DirectResolveStrategy().resolve(df, [make_test(_not_null)])

    assert results[0].failed_percentage == pytest.approx(25.0)


def test_execute_without_tests_returns_empty_results(df):
    result = DirectResolveStrategy().execute(df, [])

    assert result.test_results == []
    assert result.result_df is df
    assert result.metadata == {"test_indexes": {}}


def test_resolve_on_an_empty_frame_reports_no_failures(make_dataframe, make_test):
    empty = make_dataframe(rows=[])

    results = DirectResolveStrategy().resolve(empty, [make_test(_positive)])

    assert results[0].failed_percentage == pytest.approx(0.0)
    assert results[0].status == "PASS"


@pytest.mark.parametrize(
    "threshold, expected_status",
    [
        (100, "PASS"),
        # The failure ratio equal to the threshold is still accepted.
        (50, "PASS"),
        (49.9, "FAILED"),
        (25, "FAILED"),
    ],
)
def test_resolve_compares_the_ratio_against_the_threshold(
    df,
    make_test,
    threshold,
    expected_status,
):
    results = DirectResolveStrategy().resolve(
        df,
        [make_test(_positive, threshold=threshold)],
    )

    assert results[0].failed_percentage == pytest.approx(50.0)
    assert results[0].status == expected_status
