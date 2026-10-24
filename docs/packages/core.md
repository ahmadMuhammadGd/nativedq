# Core package: `dqt`

## Purpose and architectural role

`dqt` is the engine-independent core of DQT. It defines quality tests, the
executor and strategy contracts, result models, executor discovery, and the
ODCS contract integration. Execution engines are provided by separate adapter
packages. See [Core and adapter architecture](../architecture/core-adapter.md).

## Responsibilities and boundaries

Responsibilities:

- `@dq_test` decorator and `DQTest` test definitions.
- Argument binding and per-call threshold carrier (`DQTestCall`).
- Executor and strategy abstract base classes.
- Result models: `DQExecutionResult` and `DQTestResult`.
- Runtime discovery of installed executors through the `dqt.executors`
  entry-point group.
- ODCS v3.2.0 contract loading, validation, rule resolution, and execution
  orchestration.
- An optional benchmark harness (`dqt.benchmark`) for measuring executor
  strategies.

Boundaries:

- No Spark, pandas, or other engine imports are required by the default
  install. Engine-specific benchmark dependencies are behind the `benchmark`
  extra.
- No import of an adapter package and no execution logic for a specific engine.
- ODCS rule execution delegates to the supplied executor; the core does not
  compile expressions or scan data.

## Installation and dependencies

`requires-python = ">=3.12"`.

Required runtime dependencies:

| Dependency | Constraint | Used for |
| --- | --- | --- |
| `jsonschema` | `>=4.19` | validating contracts against the ODCS JSON Schema |
| `open-data-contract-standard` | `>=3.2.0,<3.3` | official ODCS model and bundled v3.2.0 schema |
| `pydantic` | `>=2.13.4` | test, result, and configuration models |
| `pyyaml` | `>=6.0` | parsing YAML contracts |

Optional extra:

| Extra | Adds | Needed for |
| --- | --- | --- |
| `benchmark` | `matplotlib`, `pyspark`, `requests` | importing or running `dqt.benchmark.*` |

Installing the core does not install an execution engine or discover an
executor. See the [installation guide](../guides/installation.md) for build and
install commands.

## Public APIs and extension points

### Test definition

| API | Module | Description |
| --- | --- | --- |
| `dq_test(...)` | `dqt` / `dqt.decorators` | decorator that wraps a callable in `DQTest` |
| `DQTest` | `dqt.definitions` | pydantic model holding `func`, `name`, `description`, `target_engine` |
| `DQTest.test_parameters` | computed | `DQTestParameter` list derived from the function signature |
| `DQTest.__call__` | | binds arguments and returns a `DQTestCall` |
| `DQTestCall` | `dqt.models` | bound call carrying parameter values and `maximum_accepted_error_percentage` (default 100) |

The decorator does not register tests globally. Using it as
`@dq_test` wraps the function immediately; `@dq_test(name=..., description=...,
target_engine=...)` is the configured form.

Because `DQTest` is a pydantic model, subclasses can add fields and override
`__call__`. The ODCS integration does this in `ContractDQTest` to carry rule
arguments and a threshold.

### Execution contracts

| API | Module | Description |
| --- | --- | --- |
| `DQExecutor[T]` | `dqt.abc.dqt_execute` | abstract `run(df, tests, resolve=False) -> DQExecutionResult[T]` |
| `DQExecutorConfig` | `dqt.abc.dqt_execute` | pydantic base model with arbitrary types allowed |
| `DQExecutionStrategy[T]` | `dqt.abc.dqt_execution_strategy` | abstract `execute(...)` and `resolve(...)` |
| `DQExecutionResult[T]` | `dqt.execution` | `uuid`, `test_results`, `result_df`, `metadata` |
| `DQTestResult` | `dqt.execution` | `test`, `status` (`PASS`/`FAILED`), `failed_percentage`, `failed_rows`, `evaluated_rows` |

`DQTestResult.status` is `FAILED` when `failed_percentage` is strictly greater
than the test's `maximum_accepted_error_percentage`; equality passes.
`failed_rows` is a count of failing rows for one test, not a count of failed
tests.

### Executor discovery

| API | Module | Description |
| --- | --- | --- |
| `EXECUTOR_ENTRY_POINT_GROUP` | `dqt.runtime.loaders` | `"dqt.executors"` |
| `discover_executors()` | `dqt.runtime.loaders` | returns `{name: executor_class}`; raises on duplicate names |
| `load_executor(name, config)` | `dqt.runtime.loaders` | instantiates a discovered executor; raises with available names when unknown |

To add an executor, implement `DQExecutor` (and optionally
`DQExecutionStrategy`) in an adapter package and register it:

```toml
[project.entry-points."dqt.executors"]
my_engine = "my_package:MyExecutor"
```

### ODCS integration

Exported from `dqt.odcs`:

- `ODCSContract` (`load(path)`, `from_string(text, source=None)`,
  `quality_rules()`).
- `ContractQualityRule`, `ContractDQTest`.
- `resolve_tests(contract)` and `execute_contract(contract, executor, *,
  resolve=True)`.
- `SUPPORTED_ODCS_VERSION` (`"v3.2.0"`).
- Errors: `ContractError`, `ContractValidationError`,
  `UnsupportedODCSVersionError`, `ContractRuleError`.

See the [ODCS reference](../reference/odcs.md) for the supported subset.

## Minimal usage

Defining and binding a test:

```python
from functools import partial

from dqt import dq_test
from pyspark.sql import functions as F


@dq_test
def positive(column: str):
    """column must be positive"""
    return F.col(column) > 0


# Executors call test definitions with no arguments, so bind required
# arguments when executing without ODCS.
positive_value = dq_test(name="positive_value")(partial(positive.func, column="value"))

call = positive_value(maximum_accepted_error_percentage=5)
print(call.maximum_accepted_error_percentage)  # 5
```

Running through a discovered adapter:

```python
from dqt.runtime.loaders import load_executor
from dqt_spark35_executor import Spark35ExecutorConfig

executor = load_executor("spark35", Spark35ExecutorConfig(df=source_df))
result = executor.run(tests=[positive_value], resolve=True)

for test_result in result.test_results:
    print(test_result.test.name, test_result.status, test_result.failed_rows)

result.result_df.show()  # contains the adapter's failure representation
```

The core itself cannot execute tests without an installed adapter.

## Configuration and options

The core defines no runtime configuration of its own. Executors supply their
configuration by subclassing `DQExecutorConfig`; configuration options are
documented in [Configuration](../reference/configuration.md).

Constants:

- `EXECUTOR_ENTRY_POINT_GROUP = "dqt.executors"`.
- `SUPPORTED_ODCS_VERSION = "v3.2.0"`.
- `DQT_ENGINE = "dqt"` and `MAXIMUM_ACCEPTED_ERROR_PROPERTY =
  "maximum_accepted_error_percentage"` in the ODCS resolver.

## Compatibility constraints

- Python `>=3.12`.
- Pydantic v2 models.
- ODCS v3.2.0 only; the dependency is bounded below `<3.3` because the bundled
  schema is authoritative.
- Core version is `0.1.0`; adapters declare `dqt>=0.1,<0.2`. A breaking core
  change requires a matching adapter range update.

## Testing and development

```bash
uv run pytest packages/dqt-core/src/tests
```

Core tests use pytest and do not require Spark or an adapter. The repository's
`uv sync` installs the workspace dev group, which includes pytest and the Spark
adapter for the example and integration tests. See the
[development guide](../guides/development.md).

## Known limitations

- No artifact or metric-persistence layer is implemented. `DQExecutionResult`
  is in-memory; persisting results is the caller's responsibility.
- A plain `DQTest` with required function parameters cannot be executed
  directly, because executors invoke it with no arguments. Bind arguments with
  defaults or `functools.partial`, or execute the test through an ODCS contract
  that supplies `customProperties`.
- Strategies read the threshold by calling `test()` with no arguments; a plain
  `DQTest` therefore carries the default 100 unless its `__call__` supplies
  another value (as `ContractDQTest` does).
- `target_engine` is metadata on `DQTest`; the core does not enforce it.
- Parameter annotations are exposed as `DQTestParameter` metadata but are not
  validated.
- `dqt.benchmark` is an internal benchmark harness, is not part of the stable
  public API, and requires the `benchmark` extra.
- The ODCS integration executes only `type: custom` rules with `engine: dqt`;
  other rule types are rejected rather than skipped.
