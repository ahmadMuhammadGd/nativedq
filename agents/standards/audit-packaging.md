# Task: Audit and Align `pyproject.toml` Files with the Core–Adapter Architecture

## Objective

Inspect every `pyproject.toml` in the repository and determine whether package metadata, dependencies, optional extras, workspace configuration, build settings, and installation behavior are compatible with the **core–adapter pattern**.

Make the necessary changes to align the project with the intended architecture without introducing unnecessary restructuring or breaking existing functionality.

## 1. Understand the Existing Architecture First

Before modifying anything:

- Read the repository's `AGENTS.md`, documentation, and existing architectural decisions.
- Inspect all `pyproject.toml` files and identify the packages they define.
- Inspect the actual imports, dependency relationships, build configuration, and package boundaries.
- Determine which package is the core, which packages are adapters, and which components are optional integrations.
- Verify the intended relationship between packages rather than inferring it from directory names alone.

Treat the existing implementation and documented architectural decisions as the source of truth. If the architecture is ambiguous, document the ambiguity and choose the least disruptive interpretation.

## 2. Enforce Core–Adapter Dependency Boundaries

Review and enforce the following principles:

**Core package**
- Contains the framework's fundamental abstractions, contracts, shared models, and engine-independent functionality where applicable.
- Must not depend on concrete adapter implementations.
- Must not require optional execution engines, storage backends, or integration-specific libraries merely to install or import the core.
- Should declare only its actual runtime dependencies.
- Must remain usable independently of any particular adapter.

**Adapter packages**
- Depend on the core package when they implement or extend its contracts.
- Declare their engine-specific and integration-specific dependencies in their own `pyproject.toml`.
- Must not introduce reverse dependencies from the core to an adapter.
- Must not depend on unrelated adapters unless an explicit, justified integration requires it.
- Must declare compatible core version constraints that reflect the project's versioning and release strategy.

**Dependency direction**

```text
Consumer / Application
        |
        v
   Core Package
        ^
        |
   Adapter Packages
        |
        v
Execution Engines / External Integrations
```

Interpret this as a dependency rule, not a requirement that every adapter depend directly on every external component shown. Validate the actual dependency graph against the repository's implementation.

## 3. Audit Every `pyproject.toml`

For each file, inspect and correct the following where applicable:

- `[build-system]`: valid build backend and build requirements.
- `[project]`: package name, version strategy, Python version constraints, metadata, and runtime dependencies.
- `dependencies`: only the dependencies genuinely required by that package.
- `[project.optional-dependencies]`: optional integrations, development dependencies, and extras where appropriate.
- `[dependency-groups]`: development, testing, linting, and typing tools, without confusing development dependencies with published runtime dependencies.
- `[tool.uv.workspace]` and `[tool.uv.sources]`: correct workspace membership, local package references, and editable development dependencies.
- Package discovery and inclusion: ensure the intended modules are included in built distributions.
- Version constraints: ensure Python, core, adapter, and engine versions are compatible.
- Package naming and import paths: ensure distribution names, import namespaces, and adapter entry points are consistent with the existing design.
- Lockfile consistency: ensure dependency changes can be resolved reproducibly.

Do not add configuration sections merely because they are listed here. Add or change only what the repository actually needs.

## 4. Preserve the Public API and Existing Build Workflow

- Do not rename packages, change import paths, redesign the architecture, or introduce a new packaging strategy unless necessary to resolve a demonstrated incompatibility.
- Preserve existing public APIs and documented installation commands.
- Do not move dependencies into optional extras if doing so would break a documented or intentional default behavior.
- Do not introduce circular dependencies, duplicate dependency declarations, or redundant compatibility layers.
- Do not pin every dependency unnecessarily.
- Avoid broad dependency upgrades. Change versions only when required for compatibility, correctness, or reproducible installation.
- Keep the existing build backend and workspace tooling unless there is a concrete reason to change them.

## 5. Validate the Changes

After editing, validate the repository using the existing tooling and supported environments.

At minimum:

1. Parse and validate every `pyproject.toml`.
2. Resolve the workspace and synchronize or lock dependencies using the repository's package manager.
3. Install the core package independently, without adapter-specific dependencies.
4. Install each adapter with its declared core dependency and required extras.
5. Build distributable artifacts for the core and each adapter.
6. Verify that the built artifacts contain the expected modules and metadata.
7. Run relevant unit tests, import checks, and existing lint/type checks.
8. Check for dependency cycles, undeclared imports, missing runtime dependencies, and accidental imports of adapters from the core.
9. Verify that documented installation commands still work.

Use the project's existing `uv` workflow if it is already the standard. Do not silently substitute another package manager.

If the environment cannot support a validation step, report it as unverified rather than claiming success.

## 6. Expected Deliverables

Provide:

1. **Audit findings:** every `pyproject.toml` inspected, its package role, and the issues identified.
2. **Changes made:** a concise explanation of each meaningful modification and its architectural justification.
3. **Dependency graph:** the resulting core–adapter dependency relationships.
4. **Validation results:** commands executed and their actual outcomes.
5. **Remaining issues:** unresolved ambiguities, compatibility risks, or checks that could not be completed.

## Acceptance Criteria

The task is complete only when:

- The core can be installed and imported without requiring concrete adapters.
- Each adapter declares its own integration dependencies and correctly depends on the core.
- The dependency graph respects the intended core–adapter boundaries.
- Workspace references, build metadata, package discovery, and version constraints are internally consistent.
- Core and adapter distributions can be built independently, where intended by the existing packaging design.
- Existing documented functionality and public APIs remain intact.
- All changes are supported by inspection or validation, not assumptions.

**Work autonomously:** inspect, modify, and validate the files directly. Do not stop after producing recommendations. Make the smallest coherent set of changes that achieves the acceptance criteria, and report any decisions that require architectural clarification.