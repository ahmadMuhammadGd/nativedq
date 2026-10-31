# Packaging standard

DQT is a `uv` workspace with one core distribution and engine/backend
distributions that extend it. See
[Core and adapter architecture](../architecture/core-adapter.md) for the
dependency rules behind this layout.

## Workspace

| Path | Distribution | Role | Default runtime dependencies |
| --- | --- | --- | --- |
| `pyproject.toml` | none (virtual workspace root) | workspace and dev tooling | none |
| `packages/nativedq-core` | `nativedq` | core | `jsonschema`, `open-data-contract-standard`, `pydantic`, `pyyaml` |
| `packages/nativedq-spark35-executor` | `nativedq-executor-spark35` | Spark 3.5 executor adapter | `nativedq`, `pyspark` |

The workspace root is a virtual project: no distribution is built from it.
Tooling used to test and lint the workspace lives in `[dependency-groups]`,
not in published runtime metadata. The root maps `nativedq` to the local core
package via `[tool.uv.sources]`, so workspace resolution never pulls a
different `nativedq` distribution from an index.

## Dependency rules

- The core declares only engine-independent runtime dependencies.
- Adapters declare their own engine dependencies and a compatible core range
  (`nativedq>=0.1,<0.2`).
- The core never imports an adapter. Adapters are discovered at runtime
  through the `nativedq.executors` entry-point group.
- Optional integration dependencies are exposed as named extras rather than
  default runtime dependencies.
- Installing the core must not install an execution engine.

## Extras

| Distribution | Extra | Adds | Needed for |
| --- | --- | --- | --- |
| `nativedq` | `benchmark` | `matplotlib`, `pyspark`, `requests` | importing/running `nativedq.benchmark.*` |
| `nativedq-executor-spark35` | `benchmark` | `nativedq[benchmark]`, `pytest` | importing/running `nativedq_spark35_executor.benchmark.*` |

```bash
pip install "nativedq[benchmark]"
pip install "nativedq-executor-spark35[benchmark]"
```

## Version constraints

- `nativedq` supports Python `>=3.12`.
- `nativedq-executor-spark35` supports Python `>=3.12` and `pyspark>=3.5,<3.6`,
  matching the packaged Spark 3.5 executor.
- `nativedq` requires `open-data-contract-standard>=3.2.0,<3.3` because contract
  validation uses the `schema.json` shipped by that release and only ODCS
  v3.2.0 is supported. Install the matching release before enabling another
  ODCS version; see [ODCS integration](../reference/odcs.md).

## Build and release

Build each distribution independently from the repository root:

```bash
uv build --package nativedq
uv build --package nativedq-executor-spark35
```

Both distributions use `hatchling`. The wheel targets include only the import
package:

- `nativedq` → `src/nativedq`
- `nativedq-executor-spark35` → `src/nativedq_spark35_executor`

Tests under each package's `src/tests` are not shipped. A package document
must be added under `docs/packages/` when a package is added.

## Known packaging risks

- The `nativedq` name on PyPI is currently owned by an unrelated project. Install
  from built wheels or local paths until distribution names are resolved;
  dependency resolution from an index would otherwise select the wrong
  package.
- The core's optional benchmark harness contains Spark-specific code. It is
  isolated through the `benchmark` extra, but moving it out of core would be a
  functional restructure.

## Development commands

```bash
uv sync
uv run pytest packages/nativedq-core/src/tests packages/nativedq-spark35-executor/src/tests
uv run python examples/odcs/run_example.py
```

`uv sync` installs both workspace members plus the default `dev` dependency
group. See the [development guide](../guides/development.md) for prerequisites
and the current linting state.
