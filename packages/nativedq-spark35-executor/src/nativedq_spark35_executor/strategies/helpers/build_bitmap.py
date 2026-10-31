from typing import List

from pyspark.sql import Column
from pyspark.sql import functions as F


def build_bitmap(
    exprs: list[Column],
    bits_per_bitmap: int = 63,
) -> List[Column]:
    bitmap_count = (len(exprs) + bits_per_bitmap - 1) // bits_per_bitmap
    bitmaps = [F.lit(0).cast("long") for _ in range(bitmap_count)]

    for i, expr in enumerate(exprs):
        bitmap_idx, bit_idx = divmod(i, bits_per_bitmap)

        failed_bit = F.when(
            expr.isNull() | (~expr),
            F.lit(1 << bit_idx).cast("long"),
        ).otherwise(F.lit(0).cast("long"))

        bitmaps[bitmap_idx] = bitmaps[bitmap_idx].bitwiseOR(failed_bit)

    return bitmaps