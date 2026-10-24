# Task: Document DQT Core Feature Implementation Status

Create `docs/reference/implementation-status.md` containing a single Markdown table with exactly two columns:

| Feature | Is implemented |
|---|---|

Infer DQT's actual core product features from previous DQT project conversations available to you, then inspect the current repository to determine which are implemented.

Focus on **user-facing data-quality capabilities and domain concepts**, not internal implementation details.

Investigate these core feature areas:

- Dataset definitions and dataset bindings.
- Data-quality test definitions using `@dq_test`.
- Test parameters and test invocation.
- Test suites and suite composition.
- Binding tests to datasets.
- Data-quality runs and run configuration.
- Run options and execution modes.
- Test execution and execution lifecycle.
- Test-level results and run-level results.
- Result statuses and severity levels.
- Result scopes and dimensions.
- Result inspection and failure identification.
- Analytical models and marts for data-quality results.
- Result persistence and retrieval.
- Artifact storage and result materialization.
- Discoverability of installed executors and artifact stores.
- ODCS contract-driven data-quality validation.
- Defining custom tests in contracts and resolving their implementations.
- Running a suite or contract through the intended user-facing workflow.
- Listing available executors and artifact stores.
- CLI functionality, if established in project history.

This list is a starting point. Retrieve previous DQT discussions to identify additional established core features or correct any inaccurate items.

**Do not treat these as core product features:** bitmap arrays, bitmap columns, Spark expression generation, individual execution strategies, benchmark implementations, package layout, dependency management, or build configuration. These are implementation or infrastructure details. Only include a technical capability if it directly represents an established user-facing DQT feature.

## Status rules

Use only `Yes`, `No`, or `Partial`.

- `Yes`: implemented and supported by sufficient evidence.
- `No`: an established core feature is not implemented.
- `Partial`: some of the intended functionality exists, but it is incomplete.

Verify the actual code, tests, and examples. Do not infer implementation from class names or documentation alone. Do not classify exploratory ideas as missing features.

## Output constraints

- Save the table to `docs/reference/implementation-status.md`.
- Include only the table: no introduction, conclusion, evidence column, priorities, or additional sections.
- Update `docs/README.md` with a link to the new document.
- Update `README.md` with a link to the new document.
- Do not modify application code or implement missing features.
- Do not stage benchmark files or outputs, and leave unrelated user changes untouched.

Create the document directly.