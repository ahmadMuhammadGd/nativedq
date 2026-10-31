from nativedq.execution import DQExecutionResult
from pyspark.sql import DataFrame


class SparkExecutionResult(DQExecutionResult[DataFrame]): ...