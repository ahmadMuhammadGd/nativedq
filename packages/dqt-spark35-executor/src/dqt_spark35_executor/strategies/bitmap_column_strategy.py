from typing import List

from dqt.definitions.dq_test import DQTest
from dqt.execution import DQExecutionResult, DQExecutionStrategy
from dqt.execution.dq_test_result import DQTestResult
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from dqt_spark35_executor.strategies.helpers.build_bitmap import build_bitmap
from dqt_spark35_executor.strategies.helpers.get_exprs import get_exprs


class BitMapColumnStrategy(DQExecutionStrategy[DataFrame]):
    def __init__(self, bits_per_bitmap: int = 63):
        if not 1 <= bits_per_bitmap <= 63:
            raise ValueError("bits_per_bitmap must be between 1 and 63")

        self.bits_per_bitmap = bits_per_bitmap
        self.result_column_prefix = "_dq_violations"

    def execute(
        self,
        df: DataFrame,
        tests: List[DQTest],
        resolve: bool = False,
    ) -> DQExecutionResult[DataFrame]:
        exprs = get_exprs(tests)
        bitmaps = build_bitmap(exprs, self.bits_per_bitmap)

        result_df = df.select(
            "*",
            *[
                bitmap.alias(f"{self.result_column_prefix}_{i}")
                for i, bitmap in enumerate(bitmaps)
            ],
        )

        return DQExecutionResult[DataFrame](
            test_results=self.resolve(result_df, tests) if resolve else [],
            result_df=result_df,
            metadata={"test_indexes": {i: t.name for i, t in enumerate(tests)}}
        )

    def resolve(
        self,
        df: DataFrame,
        tests: List[DQTest],
    ) -> List[DQTestResult]:
        if not tests:
            return []

        aggregates = []
        aliases = []

        for i, test in enumerate(tests):
            threshold = test().maximum_accepted_error_percentage
            bitmap_idx, bit_idx = divmod(i, self.bits_per_bitmap)

            failed = (
                F.shiftRight(
                    F.col(f"{self.result_column_prefix}_{bitmap_idx}"),
                    bit_idx,
                ).bitwiseAND(1) == 1
            )

            failed_alias = f"_dq_failed_{i}"
            aggregates.append(
                F.sum(F.when(failed, 1).otherwise(0)).alias(failed_alias)
            )
            aliases.append((test, threshold, failed_alias))

        row = df.agg(
            F.count(F.lit(1)).alias("_dq_total"),
            *aggregates,
        ).first()

        total = row["_dq_total"]
        results = []

        for test, threshold, failed_alias in aliases:
            failed_count = row[failed_alias] or 0
            failed_percentage = (
                failed_count / total * 100 if total else 0.0
            )

            results.append(
                DQTestResult(
                    test=test,
                    status="FAILED" if failed_percentage > threshold else "PASS",
                    failed_percentage=failed_percentage,
                    failed_rows=failed_count,
                    evaluated_rows=total,
                )
            )

        return results