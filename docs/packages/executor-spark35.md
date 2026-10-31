# Adapter package: `nativedq-executor-spark35`

## Purpose and architectural role

`nativedq-executor-spark35` executes DQT quality tests against PySpark 3.5
DataFrames. It is the engine-specific half of DQT: the core defines tests,
results, and contracts, and this adapter compiles tests into Spark expressions,
runs them, and reports per-test metrics and row-level failures.

See [Core and adapter architecture](../architecture/core-adapter.md).

## Responsibilities and boundaries

Responsibilities:

- Compile each `DQTest` into a `pyspark.sql.Column` expression using the test's
  native function.
- Evaluate tests against a Spark DataFrame without collecting rows to the
  driver.
- Preserve row-level failure attribution in bitmap columns and report per-test
  failure counts.
- Provide three execution strategies: bitmap array, bitmap column, and direct
  resolve.
- Register `spark35` in the `nativedq.executors` entry-point group.

Boundaries:

- Depends on `nativedq` for all test, result, and contract types; contains no
  contract parsing.
- Depends on `pyspark` for execution. The core does not import this package.
- Does not persist results or publish metrics; it returns `DQExecutionResult`
  with a Spark `result_df`.

## Installation and dependencies

`requires-python = ">=3.12"`.

| Dependency | Constraint | Purpose |
| --- | --- | --- |
| `nativedq` | `>=0.1,<0.2` | core contracts and models |
| `pyspark` | `>=3.5,<3.6` | Spark 3.5 runtime |

Optional extra:

| Extra | Adds | Needed for |
| --- | --- | --- |
| `benchmark` | `nativedq[benchmark]`, `pytest` | importing/running `nativedq_spark35_executor.benchmark.*` |

Spark requires a JVM. The repository's tests and example were verified with
Java 17. See the [installation guide](../guides/installation.md).

## Public APIs and extension points

| API | Module | Description |
| --- | --- | --- |
| `Spark35Executor` | `nativedq_spark35_executor` | `DQExecutor[DataFrame]` implementation |
| `Spark35ExecutorConfig` | `nativedq_spark35_executor` | configuration model and strategy factory |
| `Spark35ExecutorStrategies` | `nativedq_spark35_executor.executor` | enum of `BITMAP_ARRAY`, `BITMAP_COLUMN`, `DIRECT_RESOLVE` |
| `BitMapArrayStrategy` | `...strategies` | default strategy, one `_dq_violations` array column |
| `BitMapColumnStrategy` | `...strategies` | one bitmap column per 63-bit chunk |
| `DirectResolveStrategy` | `...strategies` | direct aggregation without a failure column |

Executor configuration is a pydantic model, so values are validated when it is
constructed.

### Entry point

```toml
[project.entry-points."nativedq.executors"]
spark35 = "nativedq_spark35_executor:Spark35Executor"
```

`nativedq.runtime.loaders.load_executor("spark35", config)` instantiates the
executor after discovery.

## Usage

```python
from nativedq import dq_test
from nativedq.runtime.loaders import load_executor
from nativedq_spark35_executor import Spark35ExecutorConfig
from nativedq_spark35_executor.executor import Spark35ExecutorStrategies
from pyspark.sql import functions as F


@dq_test(name="positive_value")
def positive(column: str = "value"):
    return F.col(column) > 0


config = Spark35ExecutorConfig(
    df=source_df,
    strategy=Spark35ExecutorStrategies.BITMAP_ARRAY,
    bits_per_bitmap=63,
)
executor = load_executor("spark35", config)

result = executor.run(tests=[positive], resolve=True)

for test_result in result.test_results:
    print(
        test_result.test.name,
        test_result.status,
        test_result.failed_rows,
        test_result.evaluated_rows,
        test_result.failed_percentage,
    )

result.result_df.select("id", "_dq_violations").show()
```

When tests require parameters, bind them before execution (executors call test
definitions with no arguments), or execute them through an ODCS contract that
supplies the arguments. See [Usage](../guides/usage.md).

## Configuration and supported options

`Spark35ExecutorConfig` options:

| Option | Default | Meaning |
| --- | --- | --- |
| `strategy` | `BITMAP_ARRAY` | one of `BITMAP_ARRAY`, `BITMAP_COLUMN`, `DIRECT_RESOLVE` |
| `use_existing_spark_session` | `True` | when true, use `df`; when false, create a session and load `path` |
| `df` | `None` | input DataFrame for the existing-session mode |
| `app_name` | `None` | Spark application name; required in new-session mode |
| `path` | `None` | data path to load; required in new-session mode |
| `format` | `None` | Spark data source format; required in new-session mode |
| `config` | `None` | list of `(key, value)` Spark configuration pairs |
| `bits_per_bitmap` | `63` | tests packed per bitmap value |

Existing-session mode raises `ValueError` when `df` is missing. New-session
mode requires `app_name`, `path`, and `format`, then reads
`spark.read.format(format).load(path)`. An unknown strategy raises `ValueError`.

The full option reference is in [Configuration](../reference/configuration.md).

## Strategies and failure representation

| Strategy | Failure output on `result_df` | `resolve` support |
| --- | --- | --- |
| `BITMAP_ARRAY` (default) | one `_dq_violations` array of long bitmaps | `resolve=False` returns no `test_results`; `resolve=True` computes them |
| `BITMAP_COLUMN` | `_dq_violations_0`, `_dq_violations_1`, ... (one per bitmap chunk) | same as above |
| `DIRECT_RESOLVE` | none; `result_df` is the input DataFrame | requires `resolve=True`; raises `ValueError` otherwise |

Bitmap semantics:

- Test `i` maps to array element `i // bits_per_bitmap` and bit
  `i % bits_per_bitmap`.
- A bit is set when the test expression is `NULL` or false. Null values are
  therefore counted as failures.
- `metadata["test_indexes"]` maps each test index to its name.
- `BitMapColumnStrategy` validates that `bits_per_bitmap` is between 1 and 63.
  `BitMapArrayStrategy` has no equivalent range check and defaults to 63.

Thresholds:

- Each test's threshold comes from
  `test().maximum_accepted_error_percentage`; the default is 100, and a value
  of `0` means any failed row fails the test.
- `status` is `FAILED` only when `failed_percentage > threshold`.
- With no rows, `failed_percentage` is `0.0`.

`resolve` performs one aggregation over the result DataFrame; the aggregate row
is the only data returned to the driver. Row-level failures stay in the
DataFrame for the caller to inspect or persist.

## Compatibility constraints

- Python `>=3.12`.
- PySpark `>=3.5,<3.6`; the distribution targets Spark 3.5 specifically.
- Core `nativedq>=0.1,<0.2`.
- The strategies use Spark SQL functions (`element_at`, `shiftRight`,
  `bitwiseAND`, `bitwiseOR`, `array`), so Spark 3.5 semantics apply.

## Testing and development

```bash
uv run pytest packages/nativedq-spark35-executor/src/tests
```

Tests start a local Spark session and set `PYSPARK_PYTHON` /
`PYSPARK_DRIVER_PYTHON` to the running interpreter. A JVM (Java 17 in this
repository) is required. The example under `examples/odcs/` exercises the
adapter end to end:

```bash
uv run python examples/odcs/run_example.py
```

## Known limitations

- Spark 3.5 only; other Spark versions are not supported by this distribution.
- `DIRECT_RESOLVE` does not produce row-level failure columns or a bitmap
  representation, so results cannot be attributed back to rows.
- No results are persisted and no metrics are published by the adapter; see the
  [packaging standard](../standards/packaging.md) for the artifact status.
- Test definitions with required arguments must be bound before direct
  execution; see [Core limitations](core.md#known-limitations).
