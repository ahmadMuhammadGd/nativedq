import pytest
from dqt_spark35_executor.strategies import BitMapColumnStrategy
from pyspark.sql import functions as F

BITMAP_COLUMNS = ["_dq_violations_0", "_dq_violations_1", "_dq_violations_2"]


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


@pytest.mark.parametrize("bits_per_bitmap", [0, 64, -1, 100])
def test_rejects_bits_per_bitmap_out_of_range(bits_per_bitmap):
    with pytest.raises(ValueError, match="between 1 and 63"):
        BitMapColumnStrategy(bits_per_bitmap=bits_per_bitmap)


@pytest.mark.parametrize("bits_per_bitmap", [1, 30, 63])
def test_accepts_bits_per_bitmap_in_range(bits_per_bitmap):
    strategy = BitMapColumnStrategy(bits_per_bitmap=bits_per_bitmap)

    assert strategy.bits_per_bitmap == bits_per_bitmap


def test_defaults_to_63_bits_per_bitmap():
    assert BitMapColumnStrategy().bits_per_bitmap == 63


def test_execute_adds_one_violation_column_per_bitmap(df, make_test):
    tests = _five_tests(make_test)

    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(df, tests)

    assert result.result_df.columns == ["id", "value", "category", *BITMAP_COLUMNS]
    assert result.test_results == []
    assert result.metadata == {
        "test_indexes": {index: test.name for index, test in enumerate(tests)}
    }


def test_execute_packs_violations_at_the_expected_bit_positions(df, make_test):
    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(df, _five_tests(make_test))

    rows = [
        tuple(row[column] for column in BITMAP_COLUMNS)
        for row in result.result_df.orderBy("id").collect()
    ]

    assert rows == [
        # value 10: ``negative`` fails in the second bitmap.
        (0b00, 0b10, 0b0),
        # value 20: same as above.
        (0b00, 0b10, 0b0),
        # NULL value: every rule fails.
        (0b11, 0b11, 0b1),
        # value -5: ``positive``, ``not_null`` and the repeated rule fail.
        (0b01, 0b00, 0b1),
    ]


def test_execute_keeps_every_row_and_column(df, make_test):
    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(df, _five_tests(make_test))

    assert result.result_df.count() == df.count()
    assert [
        row["id"] for row in result.result_df.orderBy("id").select("id").collect()
    ] == [1, 2, 3, 4]


def test_execute_uses_a_single_bitmap_when_bits_allow_it(df, make_test):
    result = BitMapColumnStrategy().execute(df, _five_tests(make_test))

    assert result.result_df.columns == ["id", "value", "category", "_dq_violations_0"]


def test_execute_without_tests_adds_no_columns(df):
    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(df, [])

    assert result.result_df.columns == ["id", "value", "category"]
    assert result.test_results == []
    assert result.metadata == {"test_indexes": {}}


def test_execute_resolves_on_the_frame_with_bitmap_columns(df, make_test):
    tests = _five_tests(make_test)

    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(df, tests, resolve=True)

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


def test_resolve_reads_violations_from_the_bitmap_columns(make_dataframe, make_test):
    frame = make_dataframe().select(
        "id",
        "value",
        F.lit(0b11).cast("long").alias("_dq_violations_0"),
    )

    results = BitMapColumnStrategy(bits_per_bitmap=2).resolve(
        frame,
        [make_test(_positive), make_test(_negative)],
    )

    # Both bits are set on every row, so both rules fail on all four rows.
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
    result = BitMapColumnStrategy(bits_per_bitmap=2).execute(
        df,
        [make_test(_positive, threshold=threshold)],
        resolve=True,
    )

    assert result.test_results[0].failed_percentage == pytest.approx(50.0)
    assert result.test_results[0].status == expected_status


def test_resolve_without_tests_returns_no_results(df):
    assert BitMapColumnStrategy().resolve(df, []) == []


def test_resolve_on_an_empty_frame_reports_no_failures(make_dataframe, make_test):
    empty = make_dataframe(rows=[])

    result = BitMapColumnStrategy().execute(
        empty,
        [make_test(_positive)],
        resolve=True,
    )

    assert result.test_results[0].failed_percentage == pytest.approx(0.0)
    assert result.test_results[0].status == "PASS"
