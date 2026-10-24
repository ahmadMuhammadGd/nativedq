import pytest
from dqt_spark35_executor.strategies import BitMapArrayStrategy
from pyspark.sql import functions as F


def _positive(column: str = "value"):
    return F.col(column) > 0


def _not_null(column: str = "value"):
    return F.col(column).isNotNull()


def _below_hundred(column: str = "value"):
    return F.col(column) < 100


def _negative(column: str = "value"):
    return F.col(column) < 0


def _five_tests(make_test):
    """Five rules over ``df``: 2, 1, 1, 3 and 2 failing rows out of four."""
    return [
        make_test(_positive, name="positive"),
        make_test(_not_null, name="not_null"),
        make_test(_below_hundred, name="below_hundred"),
        make_test(_negative, name="negative"),
        make_test(_positive, name="positive_again"),
    ]


def test_defaults_to_63_bits_per_bitmap():
    assert BitMapArrayStrategy().bits_per_bitmap == 63


def test_execute_adds_a_violation_array_column(df, make_test):
    tests = _five_tests(make_test)

    result = BitMapArrayStrategy(bits_per_bitmap=2).execute(df, tests)

    assert result.result_df.columns == ["id", "value", "category", "_dq_violations"]
    assert result.test_results == []
    assert result.metadata == {
        "test_indexes": {index: test.name for index, test in enumerate(tests)}
    }


def test_execute_packs_violations_into_array_elements(df, make_test):
    result = BitMapArrayStrategy(bits_per_bitmap=2).execute(df, _five_tests(make_test))

    rows = [row["_dq_violations"] for row in result.result_df.orderBy("id").collect()]

    assert rows == [
        # value 10: only ``negative`` fails, in the second array element.
        [0b00, 0b10, 0b0],
        # value 20: same as above.
        [0b00, 0b10, 0b0],
        # NULL value: every rule fails.
        [0b11, 0b11, 0b1],
        # value -5: ``positive``, ``not_null`` and the repeated rule fail.
        [0b01, 0b00, 0b1],
    ]


def test_execute_keeps_every_row_and_column(df, make_test):
    result = BitMapArrayStrategy(bits_per_bitmap=2).execute(df, _five_tests(make_test))

    assert result.result_df.count() == df.count()
    assert [
        row["id"] for row in result.result_df.orderBy("id").select("id").collect()
    ] == [1, 2, 3, 4]


def test_execute_uses_a_single_array_element_when_bits_allow_it(df, make_test):
    result = BitMapArrayStrategy().execute(df, _five_tests(make_test))

    rows = [row["_dq_violations"] for row in result.result_df.orderBy("id").collect()]

    assert all(len(values) == 1 for values in rows)
    assert rows == [
        # Only ``negative`` (bit 3) fails for 10 and 20.
        [0b01000],
        [0b01000],
        # NULL value fails every rule.
        [0b11111],
        # -5 fails ``positive`` (bit 0) and ``positive_again`` (bit 4).
        [0b10001],
    ]


def test_execute_without_tests_adds_an_empty_array_column(df):
    result = BitMapArrayStrategy().execute(df, [])

    assert result.result_df.columns == ["id", "value", "category", "_dq_violations"]
    assert result.test_results == []
    rows = [row["_dq_violations"] for row in result.result_df.collect()]
    assert rows == [[]] * 4


def test_execute_resolves_on_the_frame_with_the_array_column(df, make_test):
    result = BitMapArrayStrategy(bits_per_bitmap=2).execute(
        df, _five_tests(make_test), resolve=True
    )

    assert [item.test.name for item in result.test_results] == [
        "positive",
        "not_null",
        "below_hundred",
        "negative",
        "positive_again",
    ]
    assert [item.failed_percentage for item in result.test_results] == [
        pytest.approx(50.0),
        pytest.approx(25.0),
        pytest.approx(25.0),
        pytest.approx(75.0),
        pytest.approx(50.0),
    ]
    assert [item.status for item in result.test_results] == ["PASS"] * 5


def test_resolve_reads_violations_from_the_array(make_dataframe, make_test):
    frame = make_dataframe().select(
        "id",
        "value",
        F.array(F.lit(0b11).cast("long")).alias("_dq_violations"),
    )

    results = BitMapArrayStrategy(bits_per_bitmap=2).resolve(
        frame,
        [make_test(_positive), make_test(_negative)],
    )

    assert [item.failed_percentage for item in results] == [
        pytest.approx(100.0),
        pytest.approx(100.0),
    ]


@pytest.mark.parametrize(
    "threshold, expected_status",
    [
        (100, "PASS"),
        (50, "PASS"),
        (49.9, "FAILED"),
    ],
)
def test_resolve_compares_the_ratio_against_the_threshold(
    df,
    make_test,
    threshold,
    expected_status,
):
    result = BitMapArrayStrategy(bits_per_bitmap=2).execute(
        df,
        [make_test(_positive, threshold=threshold)],
        resolve=True,
    )

    assert result.test_results[0].failed_percentage == pytest.approx(50.0)
    assert result.test_results[0].status == expected_status


def test_resolve_without_tests_returns_no_results(df):
    assert BitMapArrayStrategy().resolve(df, []) == []


def test_resolve_on_an_empty_frame_reports_no_failures(make_dataframe, make_test):
    empty = make_dataframe(rows=[])

    result = BitMapArrayStrategy().execute(
        empty,
        [make_test(_positive)],
        resolve=True,
    )

    assert result.test_results[0].failed_percentage == pytest.approx(0.0)
    assert result.test_results[0].status == "PASS"
