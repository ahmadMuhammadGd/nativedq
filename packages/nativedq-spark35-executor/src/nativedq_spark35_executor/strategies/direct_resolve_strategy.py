from typing import List

from nativedq.definitions.dq_test import DQTest
from nativedq.execution import DQExecutionResult, DQExecutionStrategy
from nativedq.execution.dq_test_result import DQTestResult
from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from nativedq_spark35_executor.strategies.helpers.get_exprs import get_exprs


class DirectResolveStrategy(DQExecutionStrategy[DataFrame]):
    def execute(
        self,
        df: DataFrame,
        tests: List[DQTest],
        resolve: bool = True,
    ) -> DQExecutionResult[DataFrame]:
        if not resolve:
            raise ValueError(
                "Direct resolve strategy requires resolve=True"
            )

        test_results = self.resolve(df, tests)

        return DQExecutionResult[DataFrame](
            test_results=test_results,
            result_df=df,
            metadata={"test_indexes": {i: t.name for i, t in enumerate(tests)}}
        )

    def resolve(
        self,
        df: DataFrame,
        tests: List[DQTest],
    ) -> List[DQTestResult]:
        if not tests:
            return []

        exprs = get_exprs(tests)
        aggregates = []
        aliases = []

        for i, (test, expr) in enumerate(zip(tests, exprs)):
            threshold = test().maximum_accepted_error_percentage
            failed_alias = f"_dq_failed_{i}"

            aggregates.append(
                F.sum(
                    F.when(
                        expr.isNull() | (~expr),
                        1,
                    ).otherwise(0)
                ).alias(failed_alias)
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
                    status=(
                        "FAILED"
                        if failed_percentage > threshold
                        else "PASS"
                    ),
                    failed_percentage=failed_percentage,
                    failed_rows=failed_count,
                    evaluated_rows=total,
                )
            )

        return results