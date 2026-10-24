"""Run the example ODCS contract against a small local Spark DataFrame."""

import os
import sys
from pathlib import Path

from dqt.odcs import ODCSContract, execute_contract
from dqt.runtime.loaders import load_executor

from dqt_spark35_executor import Spark35ExecutorConfig
from pyspark.sql import SparkSession

HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "customers.odcs.yaml"


def main() -> None:
    # The contract references ``quality.not_null`` and ``quality.positive``.
    sys.path.insert(0, str(HERE))

    # Spark workers must use the interpreter running this example.
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    spark = (
        SparkSession.builder.master("local[1]")
        .appName("dqt-odcs-example")
        .config("spark.ui.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        df = spark.createDataFrame(
            [
                (1, "ada@example.com", 34),
                (2, None, 28),
                (3, "grace@example.com", None),
                (4, "alan@example.com", -5),
            ],
            "id int, email string, age int",
        )

        contract = ODCSContract.load(CONTRACT_PATH)

        """
        You can also import executor directly

        from dqt_spark35_executor import Spark35Executor
        spark_executor = Spark35Executor(Spark35ExecutorConfig(df=df))
        """

        spark_executor = load_executor(name="spark35", config=Spark35ExecutorConfig(df=df))
        result = execute_contract(contract, spark_executor)

        print(f"Contract {contract.contract.id} ({contract.contract.apiVersion})")
        print()

        for item in result.test_results:
            test = item.test
            print(f"{test.contract_rule_id} -> {test.name}")
            print(
                f"  {item.status}: "
                f"{item.failed_rows}/{item.evaluated_rows} rows failed "
                f"({item.failed_percentage:.1f}%)"
            )

        print()
        print("Row-level failures per test index (_dq_violations bitmaps):")
        for row in result.result_df.orderBy("id").collect():
            print(f"  id={row['id']}: {row['_dq_violations']}")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
