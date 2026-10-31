# Usage

## Define quality tests

Tests are ordinary Python functions decorated with `@dq_test`. The function
returns a native engine expression; DQT does not interpret a separate rule
language.

```python
from nativedq import dq_test
from pyspark.sql import functions as F


@dq_test
def not_null(column: str = "email"):
    """email must not be null"""
    return F.col(column).isNotNull()


@dq_test(name="positive_value", description="value must be positive")
def positive(column: str = "value"):
    return F.col(column) > 0
```

Executors invoke test definitions with no arguments. Give parameters defaults,
or bind them with `functools.partial` before executing directly:

```python
from functools import partial

from nativedq import dq_test

age_positive = dq_test(name="age_positive")(partial(positive.func, column="age"))
```

When tests are referenced from an ODCS contract, the contract's
`customProperties` supply the arguments instead; see the
[ODCS reference](../reference/odcs.md).

## Execute tests with Spark

```python
from nativedq.runtime.loaders import load_executor
from nativedq_spark35_executor import Spark35ExecutorConfig
from nativedq_spark35_executor.executor import Spark35ExecutorStrategies

executor = load_executor(
    "spark35",
    Spark35ExecutorConfig(
        df=source_df,
        strategy=Spark35ExecutorStrategies.BITMAP_ARRAY,
    ),
)

result = executor.run(tests=[not_null, age_positive], resolve=True)

for item in result.test_results:
    print(
        item.test.name,
        item.status,
        f"{item.failed_rows}/{item.evaluated_rows} failed",
        f"{item.failed_percentage:.1f}%",
    )

result.result_df.show()
```

With `resolve=False` (the executor default), execution returns the failure
representation without per-test metrics. With `DIRECT_RESOLVE`, pass
`resolve=True`; the strategy raises `ValueError` otherwise.

Inspect row-level failures with the bitmap strategy:

```python
result.result_df.select("id", "_dq_violations").show()
```

Test `i` maps to bit `i % bits_per_bitmap` of array element
`i // bits_per_bitmap`; `result.metadata["test_indexes"]` maps indexes to
names. With the default `bits_per_bitmap=63`, test `i` uses bit `i % 63` of
element `i // 63`. A set bit means the test expression was false or NULL for
that row.

## Execute an ODCS contract

```python
from nativedq.odcs import ODCSContract, execute_contract
from nativedq.runtime.loaders import load_executor
from nativedq_spark35_executor import Spark35ExecutorConfig

contract = ODCSContract.load("customers.odcs.yaml")
executor = load_executor("spark35", Spark35ExecutorConfig(df=source_df))

result = execute_contract(contract, executor)
```

`execute_contract` resolves every contract rule to a `DQTest` before running
anything, then calls the executor's existing `run` method. Unsupported or
unresolvable rules raise `ContractRuleError` instead of being skipped. Details
of the supported subset, metadata, and error handling are in the
[ODCS reference](../reference/odcs.md).

To resolve rules without executing them:

```python
from nativedq.odcs import resolve_tests

tests = resolve_tests(contract)
```

## Runnable ODCS example

The repository contains a complete example in `examples/odcs/`:

- `customers.odcs.yaml` — ODCS v3.2.0 contract with two rules.
- `quality.py` — the `@dq_test` implementations.
- `run_example.py` — loads the contract and executes it against a small local
  Spark DataFrame.

Run it from the repository root:

```bash
uv run python examples/odcs/run_example.py
```

The contract references tests by Python import path using the standard ODCS
custom-rule fields:

```yaml
type: custom
engine: nativedq
implementation: quality.not_null
```

The ODCS rule `id` (`customer_email_not_null`) is independent of the Python
test name (`not_null`). Arguments and thresholds use standard
`customProperties`:

```yaml
customProperties:
  - property: column
    value: email
  - property: maximum_accepted_error_percentage
    value: 0
```

Expected output:

```text
Contract customers-quality (v3.2.0)

customer_email_not_null -> not_null
  FAILED: 1/4 rows failed (25.0%)
customer_age_positive -> positive
  FAILED: 2/4 rows failed (50.0%)

Row-level failures per test index (_dq_violations bitmaps):
  id=1: [0]
  id=2: [1]
  id=3: [2]
  id=4: [2]
```

Row 2 has no email; rows 3 and 4 fail the age rule because a NULL age counts as
a failure and `-5` is not positive.

## Related documents

- [Configuration reference](../reference/configuration.md)
- [Core package](../packages/core.md)
- [Spark executor package](../packages/executor-spark35.md)
- [ODCS reference](../reference/odcs.md)
