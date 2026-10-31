# Installation

## Prerequisites

- Python 3.12 (`requires-python = ">=3.12"` for both distributions).
- [uv](https://docs.astral.sh/uv/) for workspace development.
- A JVM for running Spark tests or the Spark executor. The repository was
  verified with Java 17.

## Repository workspace

From the repository root:

```bash
uv sync
```

This creates `.venv`, installs both workspace members in editable mode
(`nativedq` and `nativedq-executor-spark35`), and installs the default `dev` dependency
group. No package needs to be built or installed manually for development.

Verify the environment:

```bash
uv run python -c "import nativedq; from nativedq.runtime.loaders import discover_executors; print(list(discover_executors()))"
```

Expected output for the full workspace: `['spark35']`.

## Installing the core only

The core deliberately installs without an execution engine. Install a built
wheel:

```bash
uv build --package nativedq
python -m pip install dist/nativedq-0.1.0-py3-none-any.whl
```

Or install the package directory directly:

```bash
python -m pip install ./packages/nativedq-core
```

Check that the core is usable and that no executor is discovered:

```bash
python -c "import nativedq, nativedq.odcs; from nativedq.runtime.loaders import discover_executors; print(discover_executors())"
```

Expected: `{}`.

The core's runtime dependencies are `jsonschema`, `open-data-contract-standard`
(`>=3.2.0,<3.3`), `pydantic`, and `pyyaml`.

## Installing the Spark adapter

The adapter depends on `nativedq>=0.1,<0.2` and `pyspark>=3.5,<3.6`:

```bash
uv build --package nativedq-executor-spark35
python -m pip install dist/nativedq_executor_spark35-0.1.0-py3-none-any.whl
```

When installing from built wheels, install the core wheel first so the
adapter's `nativedq` requirement is satisfied by the local package rather than by an
index lookup:

```bash
python -m pip install dist/nativedq-0.1.0-py3-none-any.whl
python -m pip install dist/nativedq_executor_spark35-0.1.0-py3-none-any.whl
```

Verify discovery:

```bash
python -c "from nativedq.runtime.loaders import discover_executors; print(discover_executors())"
```

## Optional extras

| Extra | Install command | Enables |
| --- | --- | --- |
| `nativedq[benchmark]` | `pip install "nativedq[benchmark]"` | `nativedq.benchmark.*` |
| `nativedq-executor-spark35[benchmark]` | `pip install "nativedq-executor-spark35[benchmark]"` | Adapter benchmark modules |

The adapter's `benchmark` extra includes `nativedq[benchmark]` and `pytest`.

## Distribution-name caveat

The `nativedq` name on PyPI is owned by an unrelated project. Do not rely on
resolving `nativedq` from an index: use the workspace source mapping, a built wheel,
or a local path. See the [packaging standard](../standards/packaging.md#known-packaging-risks).
