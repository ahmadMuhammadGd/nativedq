from datetime import datetime

import pytest
from dqt.abc.dqt_execute import DQExecutor
from dqt.execution import DQExecutionResult
from dqt.odcs import ODCSContract, execute_contract
from dqt.odcs.errors import ContractRuleError

RULES_SOURCE = """
from dqt import dq_test


@dq_test
def value_not_null(column: str):
    \"\"\"value must not be null\"\"\"
    return column
"""


class RecordingExecutor(DQExecutor):
    """Capture executor calls and return an empty DQT execution result."""

    def __init__(self):
        self.calls = []

    def run(self, tests, resolve=False):
        self.calls.append({"tests": tests, "resolve": resolve})
        return DQExecutionResult(test_results=[], result_df=None)


def _contract(build_contract, implementation: str) -> ODCSContract:
    return ODCSContract.from_string(
        build_contract(f"""
            - id: customer_email_not_null
              type: custom
              engine: dqt
              implementation: {implementation}
              description: customer email must be present
              severity: error
              dimension: completeness
              customProperties:
                - property: column
                  value: email
                - property: maximum_accepted_error_percentage
                  value: 1
            """),
        source="contract.yaml",
    )


def test_executes_resolved_tests_through_the_executor(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    executor = RecordingExecutor()

    result = execute_contract(
        _contract(build_contract, f"{module}.value_not_null"),
        executor,
    )

    assert isinstance(result, DQExecutionResult)
    assert len(executor.calls) == 1
    assert executor.calls[0]["resolve"] is True
    assert [test.contract_rule_id for test in executor.calls[0]["tests"]] == [
        "customer_email_not_null"
    ]


def test_preserves_contract_and_rule_attribution_in_result_metadata(
    build_contract,
    rule_module,
):
    module = rule_module(RULES_SOURCE)
    implementation = f"{module}.value_not_null"

    result = execute_contract(
        _contract(build_contract, implementation),
        RecordingExecutor(),
    )

    metadata = result.metadata["odcs"]

    datetime.fromisoformat(metadata.pop("executed_at"))

    assert metadata == {
        "contract": {
            "id": "contract-1",
            "version": "1.0.0",
            "apiVersion": "v3.2.0",
            "name": "test contract",
            "source": "contract.yaml",
            "schema": [{"name": "customers", "physicalName": None}],
        },
        "rules": [
            {
                "index": 0,
                "rule_id": "customer_email_not_null",
                "implementation": implementation,
                "location": "schema[0].quality[0]",
                "test_name": "value_not_null",
                "description": "customer email must be present",
                "severity": "error",
                "dimension": "completeness",
                "maximum_accepted_error_percentage": 1.0,
            }
        ],
    }


def test_forwards_resolve_false_to_the_executor(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    executor = RecordingExecutor()

    result = execute_contract(
        _contract(build_contract, f"{module}.value_not_null"),
        executor,
        resolve=False,
    )

    assert executor.calls[0]["resolve"] is False
    assert result.metadata["odcs"]["rules"][0]["rule_id"] == ("customer_email_not_null")


def test_unresolvable_rules_prevent_execution(build_contract):
    executor = RecordingExecutor()

    with pytest.raises(ContractRuleError):
        execute_contract(
            _contract(build_contract, "missing_module.rule"),
            executor,
        )

    assert executor.calls == []
