# Core and adapter architecture

DQT separates engine-independent framework code from engine-specific execution.
The dependency direction is one-way: adapters depend on the core, never the
reverse.

```text
Consumer / application
        │
        ▼
      nativedq  (core: models, contracts, results, plugin loading, ODCS parsing)
        ▲
        │
nativedq-executor-spark35  (adapter: Spark 3.5 execution)
        │
        ▼
     pyspark
```

## The core package (`nativedq`)

Responsibilities:

- `@dq_test` decorator and the `DQTest` / `DQTestCall` models.
- Executor and strategy abstractions (`DQExecutor`, `DQExecutorConfig`,
  `DQExecutionStrategy`).
- Result models (`DQExecutionResult`, `DQTestResult`).
- Executor discovery through the `nativedq.executors` entry-point group.
- ODCS contract loading, structural validation, rule resolution, and execution
  orchestration.
- Optional benchmark harness, installed only through the `benchmark` extra.

Boundaries:

- The core must install and import without any adapter or execution engine.
- It performs no Spark work and imports no adapter modules.
- Engine dependencies of the optional benchmark harness are declared in the
  `benchmark` extra, not in the default dependency set.
- ODCS parsing does not depend on a specific executor; rule resolution produces
  ordinary `DQTest` definitions that any executor can run.

## Adapters

Adapters implement the core's contracts for one engine or integration.

Current adapter: `nativedq-executor-spark35`.

Responsibilities:

- Depend on `nativedq` within a compatible version range and declare `pyspark` as
  its own runtime dependency.
- Compile `DQTest` definitions into native engine expressions.
- Execute tests, preserve row-level failure attribution, and resolve per-test
  result metrics.
- Register an executor under the `nativedq.executors` entry-point group.

Boundaries:

- Adapters must not be imported by the core.
- An adapter depends only on the core and its own engine; it does not depend on
  unrelated adapters.
- Engine-specific behavior stays in the adapter. The core carries no Spark
  expressions, Spark configuration, or strategy implementations.

## Plugin discovery

Executors are discovered from installed distributions at runtime:

```python
from nativedq.runtime.loaders import discover_executors, load_executor

discover_executors()          # {"spark35": Spark35Executor, ...}
load_executor("spark35", config)
```

The entry-point group is `nativedq.executors`. The Spark adapter declares:

```toml
[project.entry-points."nativedq.executors"]
spark35 = "nativedq_spark35_executor:Spark35Executor"
```

Duplicate names in the group raise an error, and an unknown name raises an
error that lists the available executors. Installing the core alone therefore
discovers no executors.

## Optional integrations

Optional dependencies are exposed as extras so that installing the core does
not pull an engine or an integration library:

| Distribution | Extra | Purpose |
| --- | --- | --- |
| `nativedq` | `benchmark` | `matplotlib`, `pyspark`, `requests` for `nativedq.benchmark` |
| `nativedq-executor-spark35` | `benchmark` | `nativedq[benchmark]` and `pytest` for the adapter's benchmark modules |

See the [packaging standard](../standards/packaging.md) for exact dependency
constraints and the [package documents](../packages/core.md) for public APIs.
