# Configuration reference

## Core

The core package has no runtime configuration options. Executors provide their
own configuration by subclassing `DQExecutorConfig`
(`nativedq.abc.dq_execute`).

| Constant | Value | Meaning |
| --- | --- | --- |
| `EXECUTOR_ENTRY_POINT_GROUP` | `nativedq.executors` | entry-point group scanned by `discover_executors()` |
| `SUPPORTED_ODCS_VERSION` | `v3.2.0` | only supported ODCS `apiVersion` |
| `DQT_ENGINE` | `nativedq` | required ODCS rule `engine` value |

## Spark 3.5 executor

`nativedq_spark35_executor.Spark35ExecutorConfig` fields:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `strategy` | `Spark35ExecutorStrategies` | `BITMAP_ARRAY` | execution strategy |
| `use_existing_spark_session` | `bool` | `True` | use `df` instead of creating a session |
| `df` | `pyspark.sql.DataFrame \| None` | `None` | input DataFrame in existing-session mode |
| `app_name` | `str \| None` | `None` | application name for new-session mode |
| `path` | `str \| None` | `None` | input path for new-session mode |
| `format` | `str \| None` | `None` | Spark data source format for new-session mode |
| `config` | `list[tuple[str, str]] \| None` | `None` | Spark configuration pairs for new-session mode |
| `bits_per_bitmap` | `int` | `63` | tests packed per bitmap value |

### DataFrame selection

- `use_existing_spark_session=True` (default): `df` is required; a missing
  value raises `ValueError`.
- `use_existing_spark_session=False`: `app_name`, `path`, and `format` are
  required; the executor builds a session with `app_name` and the supplied
  `config` pairs, then calls `spark.read.format(format).load(path)`.

### Strategies

`Spark35ExecutorStrategies` values:

| Value | Class | Failure output | `resolve` behavior |
| --- | --- | --- | --- |
| `BITMAP_ARRAY` | `BitMapArrayStrategy` | `_dq_violations` array column | optional; `False` yields no test results |
| `BITMAP_COLUMN` | `BitMapColumnStrategy` | `_dq_violations_{n}` columns | optional; `False` yields no test results |
| `DIRECT_RESOLVE` | `DirectResolveStrategy` | none (`result_df` is the input) | must be `True`; otherwise raises `ValueError` |

Additional strategy constraints:

- `BitMapColumnStrategy` requires `1 <= bits_per_bitmap <= 63`.
- Bitmap strategies map test `i` to bitmap index `i // bits_per_bitmap` and bit
  `i % bits_per_bitmap`; a bit is set when the test expression is false or
  NULL.
- `DIRECT_RESOLVE` evaluates tests with a single aggregation and does not keep
  row-level failure information.

### Thresholds

Each test call carries `maximum_accepted_error_percentage`, defaulting to 100.
A test fails when its failed-row percentage is strictly greater than the
threshold. `0` means any failing row fails the test. The comparison is strictly
greater than, so a threshold of `100` never fails (a percentage cannot exceed
100). Strategies obtain the threshold from `test()`.

For direct execution, a plain `DQTest` uses the default. The ODCS resolver
supplies thresholds from `customProperties` through `ContractDQTest`; see the
[ODCS reference](odcs.md#rule-arguments).

### Result metadata

Bitmap strategies record:

```python
{"test_indexes": {0: "first_test", 1: "second_test"}}
```

`execute_contract` adds an `odcs` entry containing the contract identity and
rule mapping; see the [ODCS results section](odcs.md#results).

## Loading executors

```python
from nativedq.runtime.loaders import discover_executors, load_executor

discover_executors()  # {"spark35": Spark35Executor}
executor = load_executor("spark35", config)
```

- The entry-point group is `nativedq.executors`.
- Duplicate entry-point names raise `ValueError`.
- An unknown executor name raises `ValueError` listing available names.
- The core installs with no executors; installing
  `nativedq-executor-spark35` registers `spark35`.

## Environment

DQT itself reads no environment variables. Spark execution may require:

| Variable | Purpose |
| --- | --- |
| `PYSPARK_PYTHON` | interpreter used by Spark workers; set it to the driver interpreter when they differ |
| `PYSPARK_DRIVER_PYTHON` | interpreter used for the Spark driver |

The repository's tests and the ODCS example set these to the running
interpreter. A compatible JDK is also required; the repository was verified
with Java 17.
