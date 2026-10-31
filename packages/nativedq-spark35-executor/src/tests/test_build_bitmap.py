import pytest
from nativedq_spark35_executor.strategies.helpers.build_bitmap import build_bitmap
from pyspark.sql import Column
from pyspark.sql import functions as F


def _expressions(count):
    return [F.col(f"c{index}") for index in range(count)]


def _evaluate(df, bitmaps):
    """Collect one row of bitmap values per input row, in row order."""
    frame = df.select(
        *[bitmap.alias(f"bitmap_{index}") for index, bitmap in enumerate(bitmaps)]
    ).orderBy("id")
    return [
        [row[f"bitmap_{index}"] for index in range(len(bitmaps))]
        for row in frame.collect()
    ]


@pytest.mark.parametrize(
    "expression_count, bits_per_bitmap, expected_bitmap_count",
    [
        (0, 63, 0),
        (1, 63, 1),
        (62, 63, 1),
        (63, 63, 1),
        (64, 63, 2),
        (126, 63, 2),
        (127, 63, 3),
        (4, 4, 1),
        (5, 4, 2),
        (5, 2, 3),
    ],
)
def test_packs_expressions_into_bitmaps(
    spark,
    expression_count,
    bits_per_bitmap,
    expected_bitmap_count,
):
    bitmaps = build_bitmap(_expressions(expression_count), bits_per_bitmap)

    assert len(bitmaps) == expected_bitmap_count
    assert all(isinstance(bitmap, Column) for bitmap in bitmaps)


def test_uses_63_bits_per_bitmap_by_default(spark):
    assert len(build_bitmap(_expressions(63))) == 1
    assert len(build_bitmap(_expressions(64))) == 2


def test_sets_one_bit_per_failing_expression(spark, df):
    bitmaps = build_bitmap([F.lit(False) for _ in range(5)])

    assert _evaluate(df, bitmaps) == [[0b11111]] * 4


def test_leaves_the_bitmap_at_zero_when_every_expression_passes(spark, df):
    bitmaps = build_bitmap([F.lit(True) for _ in range(5)])

    assert _evaluate(df, bitmaps) == [[0]] * 4


def test_treats_null_results_as_failures(spark, df):
    bitmaps = build_bitmap([F.col("value") > 0])

    # ``value`` is 10, 20, NULL, -5: the NULL row and the negative row fail.
    assert _evaluate(df, bitmaps) == [[0], [0], [1], [1]]


def test_encodes_each_expression_at_its_own_bit(spark, df):
    bitmaps = build_bitmap(
        [
            F.col("value") > 0,
            F.col("id") < 0,
            F.col("category").isNull(),
        ]
    )

    assert _evaluate(df, bitmaps) == [
        # ``id < 0`` and ``category IS NULL`` are both violated here.
        [0b110],
        [0b110],
        # NULL value fails the first rule too.
        [0b111],
        # value is -5 and id is 4, so only the first two rules fail.
        [0b011],
    ]


def test_restarts_bit_positions_for_each_bitmap(spark, df):
    bitmaps = build_bitmap([F.lit(False) for _ in range(3)], bits_per_bitmap=2)

    # Two bitmaps per row; the third expression reuses bit 0 of the second.
    assert _evaluate(df, bitmaps) == [[0b11, 0b1]] * 4


def test_combines_expressions_into_the_same_bitmap_with_bitwise_or(spark, df):
    bitmaps = build_bitmap(
        [
            F.lit(True),
            F.lit(False),
            F.lit(True),
            F.col("value").isNull(),
        ],
        bits_per_bitmap=2,
    )

    assert _evaluate(df, bitmaps) == [
        # ``lit(True)`` passes while ``lit(False)`` fails; ``value`` is not null.
        [0b10, 0b10],
        [0b10, 0b10],
        [0b10, 0b00],
        [0b10, 0b10],
    ]
