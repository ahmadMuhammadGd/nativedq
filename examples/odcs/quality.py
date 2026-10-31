from nativedq import dq_test
from pyspark.sql import functions as F


@dq_test
def not_null(column: str):
    """column must not be null"""
    return F.col(column).isNotNull()


@dq_test
def positive(column: str):
    """column must be positive"""
    return F.col(column) > 0
