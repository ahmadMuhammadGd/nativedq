# Architecture overview

DQT is a data quality framework for validating data where it is processed. It
executes quality checks with the native expressions of an execution engine and
keeps failed rows attributable to individual tests.

## Design goals

1. **Native tests** — developers define checks with the engine's own API (for
   example `pyspark.sql.functions`) instead of a DQT-specific rule language.
2. **Execution where the data runs** — tests run through an engine adapter
   against an existing DataFrame or engine-native source; data is not exported
   to a separate validation system.
3. **Row-level failures** — for each test, DQT records which rows failed and
   which test caused the failure, without collapsing everything to a single
   pass/fail value.
4. **Reporting-agnostic results** — execution returns ordinary in-memory
   result objects and engine-native DataFrames. Persisting or publishing them
   is left to open, external formats rather than a proprietary store.

## Execution model

```text
@dq_test function (native engine expression)
        │
        ▼
DQTest definition ── called with arguments ──▶ DQTestCall
        │                                          (values + threshold)
        ▼
DQExecutor.run(tests, resolve=...)
        │
        ├── engine adapter compiles each test into native expressions
        ├── engine evaluates tests and keeps row-level failure attribution
        └── adapter resolves per-test results (status, failed/evaluated rows)
        │
        ▼
DQExecutionResult(test_results, result_df, metadata)
```

- A test is a Python function decorated with `@dq_test`. The decorator stores
  the function in a `DQTest` model; it does not register it globally.
- Calling a `DQTest` binds its arguments and returns a `DQTestCall` carrying
  the argument values and the per-execution
  `maximum_accepted_error_percentage` threshold (default 100).
- The executor's strategy turns each call into native expressions, executes
  them, and produces `DQTestResult` objects. `status` is `FAILED` only when the
  failed-row percentage is strictly greater than the threshold.
- The result also carries `result_df`, which contains the engine-native
  failure representation (for the Spark adapter, bitmap columns), and
  `metadata` with the test index mapping.

## Contracts

**Execution contract** — run tests against data using the native capabilities
of an execution engine. `DQExecutor[T]` defines `run(df, tests, resolve)`.

**Result contract** — return deterministic per-test results plus row-level
failure information through `DQExecutionResult[T]` and `DQTestResult`.
`failed_rows` and `evaluated_rows` are counts; failed rows and failed tests are
different metrics.

**Artifact contract** — quality results should be persistable in open,
queryable formats independent of DQT and of any reporting UI. No artifact
package exists in this repository yet. Persisting `result_df` and the result
models is currently the caller's responsibility.

## Implementation status

| Capability | Status |
| --- | --- |
| `@dq_test` definitions and call binding | Implemented in core |
| Executor abstraction and entry-point discovery | Implemented in core |
| Spark 3.5 executor with three strategies | Implemented in `dqt-executor-spark35` |
| Per-test result metrics and threshold handling | Implemented in the Spark executor |
| Row-to-test attribution via bitmap columns | Implemented in the Spark executor |
| ODCS v3.2.0 contract execution | Implemented in core (`dqt.odcs`) |
| Persisted metric/artifact schema and artifact integrations | Not implemented |
| Additional execution engines | Not implemented |

## Persisted metrics and artifacts (design target)

This capability is not implemented. When an artifact integration is added, the
minimum per-test metric record should be:

- `dataset_name`
- `dataset_attributes`
- `test_name`
- `test_version`
- `scope`
- `total_rows`
- `failed_rows`
- `failure_pct`
- `threshold_pct`
- `status`
- `run_ts`

Metrics must be stored independently of any reporting or visualization system,
in an open, queryable format that can be inspected with ordinary data tools
(for example SQL, DuckDB, or a BI tool) without DQT. The expected flow is:

```text
Execution engine
      │
      ▼
   DQT run
      │
      ├── test results
      ├── run metrics
      └── row-level failures
                │
                ▼
        portable artifacts
                │
      ┌─────────┼─────────┐
      ▼         ▼         ▼
    SQL      DuckDB    BI / other
```

## Non-goals

DQT does not aim to provide:

- its own query language or universal test DSL;
- a mandatory web UI or centralized validation service;
- a complete data observability platform;
- a replacement for the execution engine;
- a prescribed visualization or alerting stack.

## Related documents

- [Core and adapter boundaries](core-adapter.md)
- [Core package](../packages/core.md)
- [Spark 3.5 executor](../packages/executor-spark35.md)
- [ODCS integration](../reference/odcs.md)
