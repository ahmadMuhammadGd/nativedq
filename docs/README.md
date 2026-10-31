# DQT documentation

This directory is the canonical home for project documentation. Start with the
[introduction](#introduction), then use the index below.

## Introduction

DQT is an open-source data quality framework that validates data where it is
processed. Quality tests are written with the execution engine's native
expressions, executed by an engine-specific adapter, and reported as per-test
results plus row-level failure information. See
[Architecture overview](architecture/overview.md).

## Index

| Area | Document | Contents |
| --- | --- | --- |
| Architecture | [Overview](architecture/overview.md) | Purpose, design goals, execution model, current status |
| Architecture | [Core and adapters](architecture/core-adapter.md) | Package boundaries, dependency direction, plugin discovery |
| Packages | [Core (`nativedq`)](packages/core.md) | Core APIs, contracts, installation, limitations |
| Packages | [Executor for Spark 3.5](packages/executor-spark35.md) | `Spark35Executor`, strategies, configuration |
| Guides | [Installation](guides/installation.md) | Workspace setup and installing packages/extras |
| Guides | [Usage](guides/usage.md) | Defining tests, executing them, ODCS example |
| Guides | [Development](guides/development.md) | Tests, builds, linting, repository layout |
| Reference | [ODCS integration](reference/odcs.md) | Supported ODCS subset, execution, errors, limitations |
| Reference | [Configuration](reference/configuration.md) | Executor configuration, strategies, thresholds |
| Reference | [Implementation status](reference/implementation-status.md) | Which user-facing features are implemented |
| Standards | [Documentation standard](standards/documentation.md) | Where documentation lives and how to maintain it |
| Standards | [Packaging standard](standards/packaging.md) | Workspace, extras, dependency boundaries, releases |
| Example | [`examples/odcs/`](../examples/odcs/) | Runnable contract-driven quality example |

## Documentation map

```text
docs/
├── README.md
├── architecture/     system design and package boundaries
├── standards/        mandatory project conventions
├── packages/         one document per Python package
├── guides/           task-oriented instructions
└── reference/        detailed technical reference
```

There is no `docs/decisions/` directory yet: no architecture decision record has
been required. Add one there when a decision needs a durable rationale beyond
the documents above.
