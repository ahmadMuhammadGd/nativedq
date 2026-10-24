# Packaging standard

DQT is a `uv` workspace with one core distribution and engine/backend
distributions that extend it. See
[Core and adapter architecture](../architecture/core-adapter.md) for the
dependency rules behind this layout.

## Workspace

| Path | Distribution | Role | Default runtime dependencies |
| --- | --- | --- | --- |
| `pyproject.toml` | none (virtual workspace root) | workspace and dev tooling | none |
| `packages/dqt-core` | `dqt` | core | `jsonschema`, `open-data-contract-standard`, `pydantic`, `pyyaml` |
| `packages/dqt-spark35-executor` | `dqt-executor-spark35` | Spark 3.5 executor adapter | `dqt`, `pyspark` |

The workspace root is a virtual project: no distribution is built from it.
Tooling used to test and lint the workspace lives in `[dependency-groups]`,
not in published runtime metadata. The root maps `dqt` to the local core
package via `[tool.uv.sources]`, so workspace resolution never pulls a
different `dqt` distribution from an index.

## Dependency rules

- The core declares only engine-independent runtime dependencies.
- Adapters declare their own engine dependencies and a compatible core range
  (`dqt>=0.1,<0.2`).
- The core never imports an adapter. Adapters are discovered at runtime
  through the `dqt.executors` entry-point group.
- Optional integration dependencies are exposed as named extras rather than
  default runtime dependencies.
- Installing the core must not install an execution engine.

## Extras

| Distribution | Extra | Adds | Needed for |
| --- | --- | --- | --- |
| `dqt` | `benchmark` | `matplotlib`, `pyspark`, `requests` | importing/running `dqt.benchmark.*` |
| `dqt-executor-spark35` | `benchmark` | `dqt[benchmark]`, `pytest` | importing/running `dqt_spark35_executor.benchmark.*` |

```bash
pip install "dqt[benchmark]"
pip install "dqt-executor-spark35[benchmark]"
```

## Version constraints

- `dqt` supports Python `>=3.12`.
- `dqt-executor-spark35` supports Python `>=3.12` and `pyspark>=3.5,<3.6`,
  matching the packaged Spark 3.5 executor.
- `dqt` requires `open-data-contract-standard>=3.2.0,<3.3` because contract
  validation uses the `schema.json` shipped by that release and only ODCS
  v3.2.0 is supported. Install the matching release before enabling another
  ODCS version; see [ODCS integration](../reference/odcs.md).

## Build and release

Build each distribution independently from the repository root:

```bash
uv build --package dqt
uv build --package dqt-executor-spark35
```

Both distributions use `hatchling`. The wheel targets include only the import
package:

- `dqt` → `src/dqt`
- `dqt-executor-spark35` → `src/dqt_spark35_executor`

Tests under each package's `src/tests` are not shipped. A package document
must be added under `docs/packages/` when a package is added.

## Known packaging risks

- The `dqt` name on PyPI is currently owned by an unrelated project. Install
  from built wheels or local paths until distribution names are resolved;
  dependency resolution from an index would otherwise select the wrong
  package.
- The core's optional benchmark harness contains Spark-specific code. It is
  isolated through the `benchmark` extra, but moving it out of core would be a
  functional restructure.

## Development commands

```bash
uv sync
uv run pytest packages/dqt-core/src/tests packages/dqt-spark35-executor/src/tests
uv run python examples/odcs/run_example.py
```

`uv sync` installs both workspace members plus the default `dev` dependency
group. See the [development guide](../guides/development.md) for prerequisites
and the current linting state.
