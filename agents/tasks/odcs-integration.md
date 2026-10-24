# Task: Implement ODCS Integration in DQT

Implement support for the Open Data Contract Standard (ODCS) in DQT, following the repository's `AGENTS.md` and existing architectural conventions.

You are authorized to modify `dqt-core` and other relevant packages as needed. However, **extend the existing architecture; do not redesign how DQT is built or executed.**

## 1. Inspect Before Implementing

Before writing code:

- Read `AGENTS.md` and all applicable nested agent instructions.
- Inspect the existing `@dq_test` decorator, test execution flow, executor interfaces, result models, artifact interfaces, and package dependencies.
- Identify how decorated tests are registered, identified, executed, and associated with failures.
- Inspect existing tests and public APIs.
- Consult the authoritative ODCS specification and JSON Schema for the version you intend to support.
- Determine which ODCS quality rules can be mapped to existing DQT capabilities.

Provide a concise implementation plan identifying the required changes, compatibility risks, and tests. Then proceed with implementation without waiting for approval for routine, backward-compatible core changes.

Do not rewrite unrelated code or introduce a parallel execution framework.

## 2. Integrate ODCS Without Introducing a DSL

ODCS must be the contract representation. DQT must continue using native execution-engine expressions for quality tests.

Do not implement a new DQT rule language, expression parser, or custom SQL abstraction.

The integration must separate:

1. ODCS contract loading and structural validation.
2. Resolution of contract rules to Python test functions.
3. Execution through the existing DQT execution pipeline.
4. Production of test results, metrics, and row-level failure artifacts.

Reuse existing interfaces wherever practical. Introduce new core abstractions only when necessary to support this workflow cleanly.

## 3. Use `@dq_test` Decorators and Import Paths

Developers must define executable quality tests using DQT's existing `@dq_test` decorator.

The YAML contract must reference these tests using explicit Python import paths. The contract must not duplicate the test implementation or introduce another way to define executable rules.

For example, the intended relationship is:

Python module:

```python
from dqt import dq_test


@dq_test
def customer_email_not_null(column: str):
    return f.col(column).isNotNull()
```

Use the standard ODCS quality-rule structure. DQT tests must be referenced through the standard `implementation` field of a custom quality rule:

- `type: custom`
- `engine: dqt`
- `implementation: <Python import path>`

Example:

```yaml
quality:
  - id: customer_email_not_null
    type: custom
    engine: dqt
    implementation: my_project.quality.customer_email_not_null
```

This example illustrates a DQT convention using standard ODCS fields. The Python import-path convention is DQT-specific, not part of the ODCS specification.

Requirements:

1. Resolve `implementation` as a Python import path to an existing function decorated with `@dq_test`.
2. Verify the resolved object is a valid DQT test before execution.
3. Preserve the ODCS quality-rule `id` independently of the Python function name.
4. Support multiple quality rules referencing different decorated tests.
5. Reject unresolved paths, invalid targets, and undecorated functions with actionable errors.
6. Execute resolved tests through the existing DQT execution pipeline.
7. Do not invent fields such as `test_ref` or `dq_test_ref`.
8. Do not redefine standard ODCS fields or introduce a second test registry.
9. Validate contracts against the selected ODCS version and preserve the semantics of standard fields.
10. Test the example against the authoritative ODCS v3.2.0 schema and the actual DQT implementation.

Do not implement an independent rule DSL. ODCS describes the contract, Python import paths identify test implementations, and `@dq_test` continues to define executable tests.

## 4. Preserve ODCS Semantics

Do not assume every ODCS quality rule is executable by DQT.

- Select and document the supported ODCS version.
- Validate contracts against the authoritative schema.
- Preserve standard ODCS fields and semantics.
- Keep Python import references in a clearly defined extension or metadata location compatible with the chosen ODCS version.
- Do not redefine standard fields to carry DQT-specific meanings.
- Reject or explicitly report unsupported executable rules.
- Never report a contract as fully passed when a required rule was skipped or could not be resolved.
- Preserve contract identity, version, rule identity, and useful source metadata in execution results where available.

If the selected ODCS version has no suitable standard field for an import path, choose a documented extension mechanism rather than modifying the standard contract schema.

## 5. Integrate With the Existing Core

You may introduce or modify core components required to support contract-driven execution, including:

- Contract loading and validation.
- Test reference resolution.
- Mapping contract rules to existing decorated tests.
- Execution orchestration through existing interfaces.
- Contract-aware result attribution.

However:

- Do not replace the existing execution pipeline with a new contract-specific runner.
- Do not create a second decorator or test-definition API.
- Do not introduce a custom binding object or universal test DSL.
- Do not force engine-specific dependencies into `dqt-core`.
- Do not couple contract parsing to Spark execution.
- Do not change the public behavior of existing DQT users who execute decorated tests without ODCS.
- Keep engine-specific execution in the existing executor packages and artifact-specific behavior in their existing integrations.

ODCS should be an additional way to select and organize existing DQT tests, not a replacement for DQT's execution architecture.

## 6. Preserve Result and Artifact Contracts

The integration must produce results through DQT's existing result and artifact interfaces.

For each executed contract rule, preserve the available information needed to determine:

- Which dataset and contract were evaluated.
- Which contract rule and decorated test were executed.
- When execution occurred.
- Whether execution succeeded, failed validation, or encountered an execution error.
- How many rows were evaluated and failed.
- Which rows failed and which test caused each failure.
- Why each row failed, to the extent supported by the test and execution engine.

Do not conflate failed rows, failed tests, unsupported rules, and execution errors.

Do not introduce an ODCS-specific result format when existing DQT artifacts can represent the information. Extend artifact schemas only when necessary, with explicit compatibility considerations.

## 7. Respect Technical Constraints

Follow the technical constraints in `AGENTS.md`.

In particular:

- Execute quality checks where the data runs.
- Prefer native engine operations.
- Avoid driver-side collection and unnecessary data movement.
- Minimize repeated scans, Spark actions, shuffles, and intermediate materialization.
- Keep intermediate failure representations memory-efficient.
- Preserve row-to-test attribution.
- Keep portable artifacts independent of the execution engine and reporting layer.
- Avoid unnecessary dependencies and infrastructure.

Do not introduce a new abstraction solely to accommodate ODCS if a small extension to an existing interface is sufficient.

## 8. Required Tests

Add tests covering at least:

**Contract handling**
- Valid contract loading.
- Invalid YAML and schema violations.
- Supported and unsupported contract features.
- Version handling.

**Import resolution**
- Valid decorated test import.
- Missing module or attribute.
- Undecorated function.
- Invalid or non-callable target.
- Duplicate references and multiple rules.
- Import resolution errors with actionable context.

**Execution**
- Correct mapping from contract rules to decorated tests.
- Execution through the existing DQT pipeline.
- Correct result attribution to contract rules and test identities.
- Validation failures versus execution errors.
- Correct handling of unsupported rules.

**Regression**
- Existing `@dq_test` usage without ODCS remains unchanged.
- Existing executors and artifact integrations continue working.
- Existing public APIs remain compatible unless a change is explicitly justified.

Use the actual supported execution engine for relevant integration tests where practical. Mocking import resolution or engine execution alone is insufficient to establish end-to-end correctness.

## 9. Definition of Done

The implementation is complete when:

- A valid ODCS YAML contract can resolve Python import paths to existing `@dq_test`-decorated functions.
- Resolved tests execute through DQT's existing execution architecture.
- Results retain contract-rule attribution and existing failure semantics.
- Unsupported or invalid references cannot silently disappear.
- Existing non-ODCS workflows remain compatible.
- Relevant tests pass, and verification commands are reported accurately.
- Documentation explains the supported ODCS version, contract structure, import-path convention, supported rules, and limitations.
- Changes contain no unrelated refactors or unnecessary dependencies.

At completion, report:
1. Architectural changes and why each was necessary.
2. A working end-to-end example of a contract and decorated test.
3. Supported ODCS features and unsupported cases.
4. Tests executed and their results.
5. Compatibility risks and known limitations.

**Final constraint:** You may change DQT's core implementation to support this feature, but you must not change DQT's fundamental architecture. Extend the existing decorator, executor, result, and artifact contracts rather than building a competing system.