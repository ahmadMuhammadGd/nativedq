import importlib
import textwrap
from uuid import uuid4

import pytest
from dqt.odcs import ODCSContract, execute_contract
from dqt.odcs.errors import ContractRuleError
from dqt_spark35_executor import Spark35Executor
from dqt_spark35_executor.executor import (
    Spark35ExecutorConfig,
    Spark35ExecutorStrategies,
)
from pyspark.errors import PySparkException

RULES_SOURCE = """
from dqt import dq_test
from pyspark.sql import functions as F


@dq_test
def value_positive(column: str):
    \"\"\"value must be positive.\"\"\"
    return F.col(column) > 0


@dq_test
def not_null(column: str):
    \"\"\"column must not be null.\"\"\"
    return F.col(column).isNotNull()


@dq_test
def value_below_hundred(column: str):
    \"\"\"value must be below one hundred.\"\"\"
    return F.col(column) < 100
"""


def _rule_module(tmp_path, monkeypatch) -> str:
    module_name = f"odcs_spark_rules_{uuid4().hex}"
    (tmp_path / f"{module_name}.py").write_text(
        textwrap.dedent(RULES_SOURCE),
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    importlib.invalidate_caches()

    return module_name


def _contract(module: str) -> ODCSContract:
    text = f"""
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
        implementation: {module}.value_positive
        description: value must be positive
        severity: error
        dimension: accuracy
        customProperties:
          - property: column
            value: value
          - property: maximum_accepted_error_percentage
            value: 0
      - id: id_not_null
        type: custom
        engine: dqt
        implementation: {module}.not_null
        customProperties:
          - property: column
            value: id
          - property: maximum_accepted_error_percentage
            value: 0
    properties:
      - name: value
        logicalType: integer
        quality:
          - id: value_below_hundred
            type: custom
            engine: dqt
            implementation: {module}.value_below_hundred
            customProperties:
              - property: column
                value: value
"""

    return ODCSContract.from_string(text, source="customers.odcs.yaml")


def _executor(df, strategy=Spark35ExecutorStrategies.BITMAP_ARRAY):
    return Spark35Executor(Spark35ExecutorConfig(df=df, strategy=strategy))


def test_executes_contract_rules_and_preserves_attribution(
    df,
    tmp_path,
    monkeypatch,
):
    module = _rule_module(tmp_path, monkeypatch)
    executor = _executor(df)

    result = execute_contract(_contract(module), executor)

    assert [item.test.contract_rule_id for item in result.test_results] == [
        "value_positive",
        "id_not_null",
        "value_below_hundred",
    ]
    # The ODCS rule id and the Python test identity stay independent.
    assert [item.test.name for item in result.test_results] == [
        "value_positive",
        "not_null",
        "value_below_hundred",
    ]
    # value is 10, 20, NULL, -5; id is 1, 2, 3, 4.
    assert [item.failed_percentage for item in result.test_results] == [
        pytest.approx(50.0),
        pytest.approx(0.0),
        pytest.approx(25.0),
    ]
    # A zero threshold must fail on any failed row; the default accepts all.
    assert [item.status for item in result.test_results] == [
        "FAILED",
        "PASS",
        "PASS",
    ]
    assert [
        (item.failed_rows, item.evaluated_rows) for item in result.test_results
    ] == [(2, 4), (0, 4), (1, 4)]


def test_preserves_contract_identity_and_rule_mapping_in_metadata(
    df,
    tmp_path,
    monkeypatch,
):
    module = _rule_module(tmp_path, monkeypatch)

    result = execute_contract(_contract(module), _executor(df))

    assert result.metadata["odcs"]["contract"] == {
        "id": "customers-quality",
        "version": "1.0.0",
        "apiVersion": "v3.2.0",
        "name": "customers",
        "source": "customers.odcs.yaml",
        "schema": [{"name": "customers", "physicalName": None}],
    }
    assert result.metadata["odcs"]["executed_at"]
    assert [
        (rule["rule_id"], rule["test_name"], rule["location"])
        for rule in result.metadata["odcs"]["rules"]
    ] == [
        ("value_positive", "value_positive", "schema[0].quality[0]"),
        ("id_not_null", "not_null", "schema[0].quality[1]"),
        (
            "value_below_hundred",
            "value_below_hundred",
            "schema[0].properties[0].quality[0]",
        ),
    ]


def test_produces_row_level_failure_bitmaps_for_contract_rules(
    df,
    tmp_path,
    monkeypatch,
):
    module = _rule_module(tmp_path, monkeypatch)

    result = execute_contract(_contract(module), _executor(df))

    assert "_dq_violations" in result.result_df.columns
    rows = [row["_dq_violations"] for row in result.result_df.orderBy("id").collect()]
    assert rows == [
        [0],
        [0],
        # NULL value fails value_positive (bit 0) and value_below_hundred
        # (bit 2); id_not_null passes.
        [0b101],
        # -5 fails value_positive.
        [0b001],
    ]


@pytest.mark.parametrize(
    "strategy",
    [
        Spark35ExecutorStrategies.BITMAP_ARRAY,
        Spark35ExecutorStrategies.BITMAP_COLUMN,
        Spark35ExecutorStrategies.DIRECT_RESOLVE,
    ],
)
def test_contract_rules_execute_through_existing_strategies(
    df,
    tmp_path,
    monkeypatch,
    strategy,
):
    module = _rule_module(tmp_path, monkeypatch)

    result = execute_contract(_contract(module), _executor(df, strategy))

    assert [item.status for item in result.test_results] == [
        "FAILED",
        "PASS",
        "PASS",
    ]


def test_engine_errors_propagate_instead_of_reporting_a_pass(
    df,
    tmp_path,
    monkeypatch,
):
    module = _rule_module(tmp_path, monkeypatch)
    contract = _contract(module)
    for rule in contract.contract.schema_[0].quality[0].customProperties or []:
        if rule.property == "column":
            rule.value = "missing_column"

    with pytest.raises(PySparkException, match="missing_column"):
        execute_contract(contract, _executor(df))


def test_unresolvable_contract_rules_do_not_run(
    df,
    tmp_path,
    monkeypatch,
):
    module = _rule_module(tmp_path, monkeypatch)
    contract = _contract(module)
    contract.contract.schema_[0].quality[0].implementation = f"{module}.missing_rule"

    with pytest.raises(ContractRuleError, match="has no attribute 'missing_rule'"):
        execute_contract(contract, _executor(df))
