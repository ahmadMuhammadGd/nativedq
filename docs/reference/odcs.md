# ODCS integration

DQT can execute quality rules declared in an
[Open Data Contract Standard (ODCS)](https://bitol-io.github.io/open-data-contract-standard/)
contract. ODCS remains the contract representation; executable tests stay
native DQT `@dq_test` definitions. The integration does not add a rule DSL, an
expression parser, or a second execution framework.

See the runnable example in
[`examples/odcs/`](../../examples/odcs/) and the
[usage guide](../guides/usage.md#execute-an-odcs-contract).

## Supported ODCS version

DQT supports **ODCS v3.2.0** only.

- Contracts are validated against the authoritative `schema.json` shipped by
  `open-data-contract-standard==3.2.0`; the dependency is constrained to
  `>=3.2.0,<3.3` for this reason.
- The root `apiVersion` must be `v3.2.0`. Other versions are rejected with
  `UnsupportedODCSVersionError`.
- Standard ODCS fields are parsed by the official `OpenDataContractStandard`
  model and preserved on the contract object. DQT only adds meaning to the
  convention described below.

The schema as published in v3.2.0 uses conditional blocks that expect schema
properties to declare `logicalType` when applicable. Contracts that omit it
fail schema validation; fix the contract rather than bypassing validation.

## Contract structure

ODCS v3.2.0 declares quality rules on `schema` objects and on schema
properties:

```yaml
version: 1.0.0
kind: DataContract
apiVersion: v3.2.0
id: customers-quality
name: customers

schema:
  - name: customers
    quality:
      - id: value_positive
        type: custom
        engine: dqt
        implementation: my_project.quality.value_positive
        customProperties:
          - property: column
            value: value
          - property: maximum_accepted_error_percentage
            value: 0
    properties:
      - name: value
        logicalType: integer
        quality:
          - id: value_below_hundred
            type: custom
            engine: dqt
            implementation: my_project.quality.value_below_hundred
            customProperties:
              - property: column
                value: value
```

Rules are collected in document order: object-level rules first, then the
rules of each property.

## Import-path convention

An executable rule must use the standard ODCS custom quality-rule fields:

```yaml
type: custom
engine: dqt
implementation: <python.module>.<attribute>
```

`implementation` resolves to an object that is already an instance of
`dqt.DQTest`, i.e. a function defined with the existing `@dq_test` decorator:

```python
from dqt import dq_test
from pyspark.sql import functions as F


@dq_test
def value_positive(column: str):
    """value must be positive"""
    return F.col(column) > 0
```

The decorator returns a `DQTest` definition; the `implementation` path points
at that definition, not at a call expression.

The ODCS rule `id` is preserved independently of the Python test name. Both are
available in execution results. Multiple rules may reference the same
implementation.

### Rule arguments

Standard ODCS `customProperties` carry the arguments passed to the test
function. Each `property` must match a parameter of the referenced test, and
each required parameter must be supplied:

```yaml
customProperties:
  - property: column
    value: email
```

`maximum_accepted_error_percentage` is reserved: it sets the rule's
per-execution failure threshold (a number between 0 and 100). When omitted, the
existing DQT default of 100 applies. A threshold of `0` means any failed row
fails the rule.

Unknown properties, duplicate properties, missing required parameters,
positional-only parameters, and invalid thresholds are rejected before
execution.

## Execution

```python
from dqt.odcs import ODCSContract, execute_contract
from dqt_spark35_executor import Spark35Executor, Spark35ExecutorConfig

contract = ODCSContract.load("customers.odcs.yaml")
executor = Spark35Executor(Spark35ExecutorConfig(df=source_df))

result = execute_contract(contract, executor)
```

`execute_contract` resolves every rule to a `DQTest`, then calls the executor's
existing `run(tests=..., resolve=True)` interface. Engine work remains in the
executor and its strategies; core only performs contract parsing, schema
validation, import resolution, and attribution. Pass `resolve=False` to skip
result resolution.

To resolve rules without running them:

```python
from dqt.odcs import resolve_tests

tests = resolve_tests(contract)  # list[ContractDQTest]
```

## Results

Execution returns the executor's normal `DQExecutionResult`; there is no
ODCS-specific result format.

- `result.test_results` contains one `DQTestResult` per executed rule, in
  contract order. Each item's `test` is a `ContractDQTest` carrying
  `contract_rule_id`, `implementation`, and `location`, alongside the normal
  DQT test identity (`name`, `description`).
- `status` and `failed_percentage` keep DQT's existing threshold semantics;
  `failed_rows` and `evaluated_rows` carry the exact counts computed by the
  strategy.
- The strategy's normal row-level failure representation (for example the
  `_dq_violations` bitmap columns) is unchanged, so failed rows remain
  attributable to rule indexes.
- `result.metadata["odcs"]` records the execution timestamp (`executed_at`),
  the evaluated contract (`id`, `version`, `apiVersion`, `name`, `source`, and
  the contract schema names), and the rule-to-test mapping (`rule_id`,
  `implementation`, `location`, `test_name`, `description`, `severity`,
  `dimension`, threshold). Existing metadata such as `test_indexes` is
  preserved.

Failed rows, failed rules, unsupported rules, and execution errors are
distinct: unsupported/unresolvable rules are rejected before execution, and
engine errors propagate instead of being reported as passes.

## Supported and unsupported rules

Supported:

- `type: custom` with `engine: dqt` and a string `implementation` that
  resolves to an `@dq_test` definition.
- Rules at schema-object and schema-property level.
- Multiple rules and repeated implementations.

Rejected with an actionable `ContractRuleError` (never silently skipped):

- `text`, `library`, and `sql` rules.
- Custom rules whose `engine` is not `dqt`.
- Missing or non-string `implementation`.
- Missing module, missing attribute, undecorated function, or any object that
  is not a `DQTest`.
- Executable rules without an `id`, or duplicate rule ids across the contract.
- Unknown/missing test parameters and invalid thresholds.

Malformed YAML, schema violations, and unsupported ODCS versions raise
`ContractValidationError` (or its `UnsupportedODCSVersionError` subclass) while
loading. All resolution problems in a contract are reported together.

## Safety boundary

Contracts are trusted configuration, on the same trust level as the code they
reference. Resolving `implementation` imports a Python module from the running
environment, which executes that module's import-time code. DQT does not
execute SQL or code embedded in the contract and does not accept arbitrary
expressions; only objects already registered as `@dq_test` definitions are
executable. Do not load contracts from untrusted sources.

## Limitations

- Only the executable subset above is compiled. Other ODCS quality rules are
  reported as unsupported rather than partially evaluated.
- Validation uses the authoritative v3.2.0 schema exactly as shipped; DQT does
  not relax or patch it.
- Rule parameters come from `customProperties`. DQT does not infer a column
  from the enclosing schema property.
- Engine-level failures (for example an unknown column) surface as the
  executor's exception. They are not converted into per-rule results, because
  doing so would require extra scans that DQT's execution model avoids.
- No persisted artifact schema is added by this integration.

## Adding a newer ODCS version

Support is intentionally pinned to one ODCS version at a time, because
validation uses the `schema.json` bundled with the installed
`open-data-contract-standard` release. To add an upcoming version:

1. Upgrade `open-data-contract-standard` in
   `packages/dqt-core/pyproject.toml` to the release that publishes the new
   schema, and refresh the lockfile.
2. Append the new `apiVersion` to `_SUPPORTED_ODCS_VERSIONS` in
   `dqt/odcs/contract.py` (and set `SUPPORTED_ODCS_VERSION` to the newest
   version).
3. Re-run the contract and Spark integration tests; schema changes may require
   updating the fixtures and the documented supported subset.
4. Update this document, including any newly unsupported or renamed ODCS
   fields.

From there, the rest of the integration is version-agnostic: import-path
resolution, `@dq_test` execution, result attribution, and metadata do not
contain `v3.2.0`-specific branches.

## Related documents

- [Core package](../packages/core.md) — `dqt.odcs` public APIs.
- [Usage](../guides/usage.md) — contract execution example.
- [ODCS example](../../examples/odcs/) — runnable end-to-end example.
