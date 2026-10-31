from datetime import UTC, datetime
from typing import Any, Dict, List

from nativedq.abc.dq_execute import DQExecutor
from nativedq.execution import DQExecutionResult
from nativedq.odcs.contract import ODCSContract
from nativedq.odcs.resolver import ContractDQTest, resolve_tests


def execute_contract(
    contract: ODCSContract,
    executor: DQExecutor,
    *,
    resolve: bool = True,
) -> DQExecutionResult:
    """Execute the contract's quality rules through an existing DQT executor.

    Rule resolution happens before the executor runs. Unsupported or
    unresolvable rules raise ``ContractRuleError``; they are never skipped.
    """

    tests = resolve_tests(contract)
    result = executor.run(tests=tests, resolve=resolve)
    result.metadata["odcs"] = _contract_metadata(contract, tests)

    return result


def _contract_metadata(
    contract: ODCSContract,
    tests: List[ContractDQTest],
) -> Dict[str, Any]:
    odcs_contract = contract.contract

    return {
        "executed_at": datetime.now(UTC).isoformat(),
        "contract": {
            "id": odcs_contract.id,
            "version": odcs_contract.version,
            "apiVersion": odcs_contract.apiVersion,
            "name": odcs_contract.name,
            "source": contract.source,
            "schema": [
                {"name": schema.name, "physicalName": schema.physicalName}
                for schema in odcs_contract.schema_ or []
            ],
        },
        "rules": [
            {
                "index": index,
                "rule_id": test.contract_rule_id,
                "implementation": test.implementation,
                "location": test.location,
                "test_name": test.name,
                "description": test.contract_rule_description,
                "severity": test.severity,
                "dimension": test.dimension,
                "maximum_accepted_error_percentage": (
                    test.maximum_accepted_error_percentage
                ),
            }
            for index, test in enumerate(tests)
        ],
    }
