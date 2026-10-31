from nativedq.definitions import DQTest
from nativedq.execution import DQExecutionResult, DQTestResult
from nativedq_spark35_executor.strategies.dq_execution_result import SparkExecutionResult


def _rule(value: int = 1):
    return value > 0


def _test_result(name="rule"):
    return DQTestResult(
        test=DQTest(func=_rule, name=name),
        status="PASS",
        failed_percentage=0.0,
    )


def test_is_a_dq_execution_result(df):
    result = SparkExecutionResult(test_results=[], result_df=df)

    assert isinstance(result, DQExecutionResult)


def test_exposes_test_results_dataframe_and_metadata(df):
    test_result = _test_result()

    result = SparkExecutionResult(
        test_results=[test_result],
        result_df=df,
        metadata={"strategy": "spark"},
    )

    assert result.test_results == [test_result]
    assert result.result_df is df
    assert result.result_df.count() == 4
    assert result.metadata == {"strategy": "spark"}


def test_metadata_defaults_to_an_empty_dict(df):
    result = SparkExecutionResult(test_results=[], result_df=df)

    assert result.metadata == {}


def test_generates_a_unique_uuid_per_result(df):
    first = SparkExecutionResult(test_results=[], result_df=df)
    second = SparkExecutionResult(test_results=[], result_df=df)

    assert isinstance(first.uuid, str)
    assert first.uuid
    assert first.uuid != second.uuid
