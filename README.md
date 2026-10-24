# DQT

DQT is an open-source data quality framework that validates data where it is
processed. Quality tests are written with the execution engine's native
expressions, executed by an engine adapter, and reported as per-test results
plus row-level failure information.

## Key capabilities

- **Native tests** — define checks as ordinary Python functions decorated with
  `@dq_test`; test bodies use PySpark expressions, not a DQT-specific DSL.
- **Execute where the data lives** — the Spark 3.5 adapter runs tests against
  an existing DataFrame without moving data to another system.
- **Row-level attribution** — bitmap columns record which rows failed and which
  test caused each failure.
- **Per-test metrics** — status, failed rows, evaluated rows, and failed
  percentage computed with a single aggregation per execution.
- **ODCS contracts** — execute ODCS v3.2.0 custom quality rules that reference
  `@dq_test` implementations by Python import path.
- **Pluggable executors** — adapters register through the `dqt.executors`
  entry-point group.

The core installs and imports without an execution engine.

## Quick start

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), and a JVM for
Spark execution (Java 17 was used for verification).

```bash
uv sync
uv run python examples/odcs/run_example.py
```

A minimal test and execution:

```python
from dqt import dq_test
from dqt.runtime.loaders import load_executor
from dqt_spark35_executor import Spark35ExecutorConfig
from pyspark.sql import functions as F


@dq_test
def positive(column: str = "value"):
    """value must be positive"""
    return F.col(column) > 0


executor = load_executor("spark35", Spark35ExecutorConfig(df=source_df))
result = executor.run(tests=[positive], resolve=True)
```

## Architecture

```text
        Application
             │
             ▼
     dqt  (core: tests, results, contracts, plugin loading)
             ▲
             │
dqt-executor-spark35  (adapter: Spark 3.5 execution)
             │
             ▼
          pyspark
```

The core never imports an adapter. See
[Core and adapter architecture](docs/architecture/core-adapter.md).

## Available adapters

Adapters provide execution for one engine and register through the
`dqt.executors` entry-point group. The core installs without any of them.

| Adapter | Engine | Package | Entry point |
| --- | --- | --- | --- |
| Spark 3.5 executor | PySpark `>=3.5,<3.6` | `dqt-executor-spark35` | `spark35` |

Spark 3.5 is the only adapter in this repository. Install it with the
workspace (`uv sync`) or from a built wheel; installing from an index is not
supported while the `dqt` distribution name is unresolved. See
[Installation](docs/guides/installation.md) and the
[Spark 3.5 executor documentation](docs/packages/executor-spark35.md).

## Documentation

All project documentation is under [`docs/`](docs/README.md):

- [Architecture overview](docs/architecture/overview.md)
- [Core package](docs/packages/core.md)
- [Spark 3.5 executor](docs/packages/executor-spark35.md)
- [Installation](docs/guides/installation.md) and
  [usage](docs/guides/usage.md)
- [ODCS integration](docs/reference/odcs.md)
- [Implementation status](docs/reference/implementation-status.md)
- [Packaging standard](docs/standards/packaging.md)
