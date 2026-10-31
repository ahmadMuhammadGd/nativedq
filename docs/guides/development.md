# Development

## Repository layout

```text
pyproject.toml                  virtual uv workspace root
packages/nativedq-core/              core distribution `nativedq`
packages/nativedq-spark35-executor/  adapter distribution `nativedq-executor-spark35`
examples/odcs/                  runnable ODCS example
docs/                           all project documentation
agents/                         agent task inputs (tooling, not project docs)
```

Tests live in each package's `src/tests` directory and are not shipped in the
built wheels.

## Setup

```bash
uv sync
```

Requires Python 3.12 and uv. Running Spark tests or the example also requires a
JVM; Java 17 was used for verification.

## Tests

Run both suites from the repository root:

```bash
uv run pytest packages/nativedq-core/src/tests packages/nativedq-spark35-executor/src/tests
```

Or run one package:

```bash
uv run pytest packages/nativedq-core/src/tests
uv run pytest packages/nativedq-spark35-executor/src/tests
```

Core tests do not require Spark. Adapter tests start a local Spark session and
set `PYSPARK_PYTHON`/`PYSPARK_DRIVER_PYTHON` to the current interpreter.

## Example

```bash
uv run python examples/odcs/run_example.py
```

The expected output is documented in [Usage](usage.md#runnable-odcs-example).

## Build

Build each distribution independently:

```bash
uv build --package nativedq
uv build --package nativedq-executor-spark35
```

Both use `hatchling`; the wheels contain only `nativedq` and
`nativedq_spark35_executor` respectively. See the
[packaging standard](../standards/packaging.md).

## Linting and formatting

`ruff` is configured in the root `pyproject.toml`; `black` is installed through
the dev dependency group. Current repository state, verified with the commands
below:

```bash
uv run ruff check packages
uv run black --check packages
```

- `ruff check` reports existing findings in source that this documentation
  work does not change.
- `black --check` reports existing formatting differences.

Do not treat these as a passing baseline. Formatting or lint fixes should be
made in changes that own those files rather than as part of documentation
edits.

## Documentation

- All documentation lives under `docs/`; start at the
  [documentation index](../README.md).
- Follow the [documentation standard](../standards/documentation.md).
- Every package has a document under `docs/packages/`.
- Update the relevant document when behavior, APIs, configuration, installation,
  or compatibility changes, and verify relative links after moving files.

## Adding a package

1. Add the distribution under `packages/` and register it in the workspace
   (`members = ["packages/*"]` handles discovery).
2. Keep the dependency direction: adapters depend on `nativedq`, never the reverse.
3. Add `docs/packages/<package>.md` covering the sections required by the
   [documentation standard](../standards/documentation.md#package-documents).
4. Link the new document from `docs/README.md`.
5. Add workspace and dependency information to the
   [packaging standard](../standards/packaging.md).
