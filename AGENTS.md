# AGENTS.md

## Project purpose

DQT is an open-source data quality framework that validates data where it is processed.

Its goals are to:

- Execute data quality tests using native engine capabilities rather than a custom DSL.
- Identify failed rows and determine what failed, when, and why.
- Publish quality metrics using open, reporting-agnostic formats.
- Minimize additional computation, data movement, storage, and operational complexity.

Treat these goals as architectural constraints, not optional preferences.

## Documentation

- `docs/` is the canonical location for all project documentation. The only
documentation allowed outside it is the root `README.md`, this file, and files
required by tooling, packaging, licensing, or external platform conventions.
- Follow `docs/standards/documentation.md` for structure, writing, and
  maintenance rules.
- Package documentation belongs in `docs/packages/`; every package requires a
document there.
- Packaging boundaries and workspace rules live in
  `docs/standards/packaging.md`.
- Update the affected documentation whenever a change alters documented
  behavior, public APIs, configuration, installation, or compatibility. Do not
  leave documentation contradicting the implementation.
- Verify relative links after moving or renaming documentation, and report any
  validation that could not be run.
- Start from `docs/README.md` to find architecture, package, guide, and
  reference material.

## Required workflow

Before modifying code:

1. Read this file and any applicable nested `AGENTS.md` files.
2. Inspect the repository structure, relevant source code, tests, dependency definitions, and current Git changes.
3. Trace the existing execution path and public interfaces affected by the task.
4. Identify the smallest change that satisfies the requirement.
5. State the intended changes, affected packages, compatibility implications, and tests before implementing non-trivial work.

Do not assume the repository matches documentation or previous AI-generated descriptions. Verify the current implementation.

## Scope control

- Change only what is necessary for the requested task.
- Do not rewrite working code merely to introduce a preferred architecture or coding style.
- Do not refactor unrelated modules, rename public interfaces, or move files without explicit justification.
- Do not add dependencies when existing functionality or the standard library is sufficient.
- Do not introduce new abstractions, registries, factories, configuration layers, or intermediate representations without demonstrating their necessity.
- Do not silently change existing behavior, defaults, return types, or public APIs.
- Preserve uncommitted user changes. Never reset, overwrite, or discard them.
- If the task requires a breaking change or a broader redesign, explain the trade-off and obtain approval before proceeding.

## Architecture and package boundaries

Respect these boundaries:

- Shared functionality belongs in core only when it is genuinely engine-independent.
- Engine-specific operations belong in the relevant executor.
- Storage-specific functionality belongs in the relevant artifact integration.
- Avoid importing optional engine or storage dependencies into core.
- Do not duplicate execution logic across packages when a small shared abstraction is sufficient.
- Do not add an engine abstraction merely to make all engines look identical.

## Open Data Contract Standard (ODCS)

ODCS is the external contract standard. DQT is responsible for executing supported quality requirements and producing execution results.

Follow these rules:

- Use the authoritative ODCS specification and its versioned schema as the source of truth.
- Pin and document the supported ODCS version. Do not mix fields or semantics from different versions.
- Preserve standard contract fields and semantics when parsing, validating, or serializing contracts.
- Do not create a competing DQT-specific contract DSL.
- Do not invent non-standard fields when an existing ODCS field or supported extension mechanism is appropriate.
- Keep contract parsing and structural validation separate from quality-rule execution.
- Keep engine-specific compilation separate from the contract's portable representation.
- Map supported quality rules to native engine operations wherever possible.
- Explicitly report unsupported rules, unsupported rule parameters, and compilation failures. Never silently skip a rule.
- Do not assume every ODCS quality rule can be executed by every engine.
- Preserve contract identity, version, rule identity, and useful source information in execution results where available.
- Do not execute arbitrary contract-supplied code or SQL without defining and enforcing the required safety boundaries.

Before implementing ODCS functionality, document the supported contract subset, its execution semantics, and how unsupported features are handled.

Do not implement the entire ODCS standard unless explicitly requested.

## Execution semantics

Preserve DQT's existing execution model unless the task explicitly changes it.

- Execute tests against the supplied DataFrame or engine-native data source.
- Avoid collecting distributed data to the driver or converting it to Pandas merely to evaluate rules or aggregate failures.
- Avoid repeated scans, unnecessary intermediate DataFrames, redundant materialization, and excessive persistence.
- Prefer native Spark expressions and aggregations for Spark execution.
- Preserve row-level failure information and per-test failure attribution wherever the existing design supports them.
- Distinguish failed-row counts from failed-test counts. They are different metrics.
- Keep metric definitions consistent across executors.
- Do not introduce a binding object, a custom expression language, or an additional execution layer without explicit architectural justification.
- Treat correctness and predictable semantics as prerequisites for performance optimization.

## Open standards and artifacts

- Prefer documented, open formats and stable schemas for persisted quality results.
- Keep reporting and visualization concerns separate from execution.
- Do not make a proprietary database, dashboard, or vendor-specific artifact format mandatory for core execution.
- Do not introduce a new artifact format when an existing supported standard satisfies the requirement.
- Version persisted schemas and preserve backward compatibility where practical.
- Avoid storing redundant row-level data when compact metrics and failure attribution meet the requirement.
- Document any unavoidable engine-specific or storage-specific extensions.

## Implementation standards

- Follow existing naming, typing, error-handling, and formatting conventions.
- Use the project's existing dependency manager and workspace configuration.
- Prefer small, explicit functions over unnecessary layers of indirection.
- Keep errors actionable and preserve their underlying causes.
- Avoid broad exception handling that hides failures.
- Do not add speculative fallback behavior.
- Do not use mocks as a substitute for testing important engine semantics.
- Do not modify dependency versions, lockfiles, build configuration, or public interfaces unless required by the task.

## Testing requirements

Every behavior change must include appropriate tests.

Depending on the change, cover:

- Normal operation and expected outputs.
- Empty inputs and boundary conditions.
- Invalid contracts and malformed configuration.
- Unsupported ODCS features and invalid rule mappings.
- Correct rule-to-engine compilation.
- Correct failed-row and failed-test aggregation.
- Compatibility with existing APIs and persisted artifacts.
- Engine-specific behavior using the actual supported engine where practical.
- Regression cases for previously supported functionality.

Use small deterministic fixtures for unit tests. Keep performance benchmarks separate from correctness tests.

Inspect the project's existing CI configuration and package scripts to determine the authoritative validation commands. Do not invent commands or claim tests passed unless they were executed successfully.

If a test cannot be run, state why and identify the remaining verification required.

## Performance and dependencies

Performance is a product requirement.

Before adding a dependency or introducing a new execution pass:

1. Explain the functionality it provides.
2. Check whether existing dependencies can provide it.
3. Assess its runtime, memory, storage, and maintenance costs.
4. Benchmark material performance changes where appropriate.

Do not optimize based on assumptions alone. Do not claim an implementation is faster without evidence.

## Definition of done

A task is complete only when:

- The requested behavior is implemented within the agreed scope.
- Existing behavior and public interfaces are preserved unless explicitly changed.
- Relevant tests are added or updated and executed where possible.
- Applicable formatting, linting, typing, and test checks have been run.
- Documentation is updated where behavior or supported features changed.
- New dependencies and compatibility implications are justified.
- Git changes have been reviewed for unrelated modifications.
- The final report states what changed, what was tested, what remains unsupported, and any known limitations.

Never claim completion based solely on generated code or a successful import.

## Handling uncertainty

When requirements, standards semantics, or existing interfaces are unclear:

- Inspect the relevant source and authoritative documentation.
- Identify the specific ambiguity and its consequences.
- Ask a focused question when the decision affects public APIs, persisted formats, compatibility, or architecture.
- Otherwise, choose the smallest reversible change consistent with existing behavior and document the assumption.

## Packaging and Dependency Architecture

- The core must not depend on concrete adapters or execution engines.
- Adapters may depend on the core, never the reverse.
- Each adapter must declare its own engine-specific runtime dependencies.
- Keep optional integrations optional; installing the core must not require them.
- Maintain consistent workspace configuration and compatible version constraints.
- Preserve existing public APIs and documented installation workflows.
- Validate packaging changes with dependency resolution, independent builds, and installation/import checks.

Do not invent requirements to make implementation easier.

See `docs/standards/packaging.md` for the workspace layout, extras, and version
constraints that implement these rules.