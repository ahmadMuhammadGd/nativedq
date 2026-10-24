
from enum import Enum
from typing import List, Optional, Tuple

from dqt.abc.dqt_execute import DQExecutor, DQExecutorConfig
from dqt.abc.dqt_execution_strategy import DQExecutionStrategy
from pyspark.sql import DataFrame, SparkSession

from dqt_spark35_executor.strategies.bitmap_array_strategy import (
    BitMapArrayStrategy,
)
from dqt_spark35_executor.strategies.bitmap_column_strategy import (
    BitMapColumnStrategy,
)
from dqt_spark35_executor.strategies.direct_resolve_strategy import (
    DirectResolveStrategy,
)


class Spark35ExecutorStrategies(Enum):
    BITMAP_ARRAY = "BITMAP_ARRAY"
    BITMAP_COLUMN = "BITMAP_COLUMN"
    DIRECT_RESOLVE = "DIRECT_RESOLVE"


class Spark35ExecutorConfig(DQExecutorConfig):
    strategy: Spark35ExecutorStrategies = Spark35ExecutorStrategies.BITMAP_ARRAY

    # Spark configuration
    use_existing_spark_session: bool = True

    app_name: Optional[str] = None
    path: Optional[str] = None
    format: Optional[str] = None
    config: Optional[List[Tuple[str, str]]] = None
    df: Optional[DataFrame] = None

    # Bitmap strategy configuration
    bits_per_bitmap: int = 63

    def get_strategy_object(self) -> DQExecutionStrategy:
        strategies = {
            Spark35ExecutorStrategies.BITMAP_ARRAY: lambda: BitMapArrayStrategy(
                self.bits_per_bitmap
            ),
            Spark35ExecutorStrategies.BITMAP_COLUMN: lambda: BitMapColumnStrategy(
                self.bits_per_bitmap
            ),
            Spark35ExecutorStrategies.DIRECT_RESOLVE: DirectResolveStrategy,
        }

        try:
            strategy_factory = strategies[self.strategy]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported strategy: {self.strategy}"
            ) from exc

        return strategy_factory()

    def _use_existing_session(self) -> DataFrame:
        if self.df is None:
            raise ValueError(
                "'df' must be provided when using an existing DataFrame."
            )

        return self.df

    def _start_new_spark_session(self) -> DataFrame:
        if not self.app_name:
            raise ValueError("'app_name' is required to create a Spark session.")

        if not self.path:
            raise ValueError("'path' is required to load a DataFrame.")

        if not self.format:
            raise ValueError("'format' is required to load a DataFrame.")

        spark_builder = SparkSession.builder.appName(self.app_name)

        for key, value in self.config or []:
            spark_builder = spark_builder.config(key, value)

        spark = spark_builder.getOrCreate()

        return spark.read.format(self.format).load(self.path)

    def get_df(self) -> DataFrame:
        if self.use_existing_spark_session:
            return self._use_existing_session()

        return self._start_new_spark_session()


class Spark35Executor(DQExecutor[DataFrame]):
    def __init__(self, config: Spark35ExecutorConfig):
        self.config = config
        self.strategy_obj: DQExecutionStrategy = config.get_strategy_object()

    def run(self, tests, resolve: bool = False):
        df = self.config.get_df()

        return self.strategy_obj.execute(
            df,
            tests=tests,
            resolve=resolve,
        )
