import json

import pytest
from dqt.odcs import ContractDQTest, ODCSContract, resolve_tests
from dqt.odcs.errors import ContractRuleError

RULES_SOURCE = """
from dqt import dq_test


@dq_test
def value_not_null(column: str):
    \"\"\"value must not be null\"\"\"
    return column


def undecorated(column: str):
    return column


NOT_A_TEST = 42


@dq_test
def positional_only(column: str, /):
    return column
"""


def _custom_rule(
    implementation: str,
    *,
    rule_id: str = "rule_one",
    properties: dict | None = None,
) -> str:
    lines = [
        f"- id: {rule_id}",
        "  type: custom",
        "  engine: dqt",
        f"  implementation: {implementation}",
    ]

    if properties:
        lines.append("  customProperties:")
        for name, value in properties.items():
            lines.append(f"    - property: {name}")
            lines.append(f"      value: {json.dumps(value)}")

    return "\n".join(lines)


def _resolve_one(build_contract, implementation, **kwargs):
    contract = ODCSContract.from_string(
        build_contract(_custom_rule(implementation, **kwargs))
    )

    return resolve_tests(contract)


def test_resolves_a_decorated_test_and_keeps_rule_id_separate_from_test_name(
    build_contract,
    rule_module,
):
    module = rule_module(RULES_SOURCE)
    implementation = f"{module}.value_not_null"

    [test] = _resolve_one(
        build_contract,
        implementation,
        rule_id="customer_email_not_null",
        properties={"column": "email"},
    )

    assert isinstance(test, ContractDQTest)
    assert test.contract_rule_id == "customer_email_not_null"
    assert test.name == "value_not_null"
    assert test.implementation == implementation
    assert test.location == "schema[0].quality[0]"
    assert test.arguments == {"column": "email"}
    assert test.description == "value must not be null"
    assert test.maximum_accepted_error_percentage == 100.0

    call = test()

    assert [(parameter.name, parameter.value) for parameter in call.parameters] == [
        ("column", "email")
    ]


def test_resolved_test_carries_arguments_and_threshold_when_executors_call_it(
    build_contract,
    rule_module,
):
    module = rule_module(RULES_SOURCE)

    [test] = _resolve_one(
        build_contract,
        f"{module}.value_not_null",
        properties={
            "column": "email",
            "maximum_accepted_error_percentage": 0,
        },
    )

    call = test()

    assert test.arguments == {"column": "email"}
    assert test.maximum_accepted_error_percentage == 0.0
    assert [(parameter.name, parameter.value) for parameter in call.parameters] == [
        ("column", "email")
    ]
    # Zero is a meaningful threshold and must not fall back to 100.
    assert call.maximum_accepted_error_percentage == 0.0


def test_resolves_multiple_rules_referencing_the_same_implementation(
    build_contract,
    rule_module,
):
    module = rule_module(RULES_SOURCE)
    implementation = f"{module}.value_not_null"
    rules = "\n".join(
        [
            _custom_rule(
                implementation, rule_id="rule_one", properties={"column": "a"}
            ),
            _custom_rule(
                implementation, rule_id="rule_two", properties={"column": "b"}
            ),
        ]
    )

    tests = resolve_tests(ODCSContract.from_string(build_contract(rules)))

    assert [test.contract_rule_id for test in tests] == ["rule_one", "rule_two"]
    assert [test.name for test in tests] == ["value_not_null", "value_not_null"]
    assert [test.arguments for test in tests] == [
        {"column": "a"},
        {"column": "b"},
    ]


def test_resolves_no_rules_to_an_empty_list(build_contract):
    assert resolve_tests(ODCSContract.from_string(build_contract())) == []


def test_rejects_an_unimportable_module(build_contract):
    with pytest.raises(ContractRuleError, match="cannot import module"):
        _resolve_one(build_contract, "module_does_not_exist.rule")


def test_reports_the_implementation_when_the_attribute_is_missing(
    build_contract,
    rule_module,
):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(ContractRuleError, match="has no attribute 'missing_rule'"):
        _resolve_one(build_contract, f"{module}.missing_rule")


def test_rejects_an_undecorated_function(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(
        ContractRuleError,
        match="not a function decorated with @dq_test",
    ):
        _resolve_one(build_contract, f"{module}.undecorated")


def test_rejects_a_non_callable_target(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(ContractRuleError, match="resolved to int"):
        _resolve_one(build_contract, f"{module}.NOT_A_TEST")


def test_rejects_a_module_that_fails_to_import(build_contract, rule_module):
    module = rule_module("""
        raise ImportError("missing dependency")
        """)

    with pytest.raises(ContractRuleError, match="failed to import"):
        _resolve_one(build_contract, f"{module}.rule")


def test_rejects_a_non_dotted_implementation(build_contract):
    with pytest.raises(ContractRuleError, match="not a dotted import path"):
        _resolve_one(build_contract, "not_a_dotted_path")


def test_rejects_an_implementation_mapping(build_contract):
    rule = """
    - id: rule_one
      type: custom
      engine: dqt
      implementation:
        path: my_package.quality.rule
    """

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="dotted Python import path"):
        resolve_tests(contract)


def test_rejects_unsupported_rule_types(build_contract):
    rule = """
    - id: row_count
      type: library
      metric: rowCount
      mustBe: 0
    """

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="type 'library'"):
        resolve_tests(contract)


def test_rejects_custom_rules_for_other_engines(build_contract):
    rule = """
    - id: soda_rule
      type: custom
      engine: soda
      implementation: soda.check
    """

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="engine 'soda'"):
        resolve_tests(contract)


def test_rejects_unknown_custom_properties(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(
        ContractRuleError,
        match="not parameters of 'value_not_null'",
    ):
        _resolve_one(
            build_contract,
            f"{module}.value_not_null",
            properties={"column": "email", "unknown": 1},
        )


def test_rejects_missing_required_test_parameters(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(
        ContractRuleError,
        match="missing required parameters",
    ):
        _resolve_one(build_contract, f"{module}.value_not_null")


def test_rejects_duplicate_custom_properties(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    rule = _custom_rule(
        f"{module}.value_not_null",
        properties={"column": "email"},
    ).replace(
        '    - property: column\n      value: "email"',
        '    - property: column\n      value: "email"\n'
        '    - property: column\n      value: "other"',
    )

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="more than once"):
        resolve_tests(contract)


def test_rejects_duplicate_threshold_properties(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    rule = (
        "- id: rule_one\n"
        "  type: custom\n"
        "  engine: dqt\n"
        f"  implementation: {module}.value_not_null\n"
        "  customProperties:\n"
        "    - property: column\n"
        "      value: email\n"
        "    - property: maximum_accepted_error_percentage\n"
        "      value: 0\n"
        "    - property: maximum_accepted_error_percentage\n"
        "      value: 5"
    )

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="more than once"):
        resolve_tests(contract)


def test_rejects_positional_only_test_parameters(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(ContractRuleError, match="positional-only"):
        _resolve_one(
            build_contract,
            f"{module}.positional_only",
            properties={"column": "email"},
        )


@pytest.mark.parametrize(
    "value, message",
    [
        ("5", "must be a number"),
        (True, "must be a number"),
        (-1, "between 0 and 100"),
        (101, "between 0 and 100"),
    ],
)
def test_rejects_invalid_thresholds(
    build_contract,
    rule_module,
    value,
    message,
):
    module = rule_module(RULES_SOURCE)

    with pytest.raises(ContractRuleError, match=message):
        _resolve_one(
            build_contract,
            f"{module}.value_not_null",
            properties={
                "column": "email",
                "maximum_accepted_error_percentage": value,
            },
        )


def test_rejects_duplicate_rule_ids(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    implementation = f"{module}.value_not_null"
    rules = "\n".join(
        [
            _custom_rule(implementation, rule_id="same_id", properties={"column": "a"}),
            _custom_rule(implementation, rule_id="same_id", properties={"column": "b"}),
        ]
    )

    with pytest.raises(ContractRuleError, match="duplicate quality rule id"):
        resolve_tests(ODCSContract.from_string(build_contract(rules)))


def test_rejects_executable_rules_without_an_id(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    rule = (
        "- type: custom\n"
        "  engine: dqt\n"
        f"  implementation: {module}.value_not_null\n"
        "  customProperties:\n"
        "    - property: column\n"
        "      value: email"
    )

    contract = ODCSContract.from_string(build_contract(rule))

    with pytest.raises(ContractRuleError, match="missing the mandatory 'id'"):
        resolve_tests(contract)


def test_reports_every_unusable_rule_together(build_contract):
    rules = "\n".join(
        [
            _custom_rule("missing_module.rule", rule_id="bad_import"),
            (
                "- id: library_rule\n"
                "  type: library\n"
                "  metric: rowCount\n"
                "  mustBe: 0"
            ),
        ]
    )

    with pytest.raises(ContractRuleError) as excinfo:
        resolve_tests(ODCSContract.from_string(build_contract(rules)))

    message = str(excinfo.value)
    assert "schema[0].quality[0]" in message
    assert "schema[0].quality[1]" in message
    assert "bad_import" in message
    assert "library_rule" in message


def test_resolves_property_level_rules(build_contract, rule_module):
    module = rule_module(RULES_SOURCE)
    contract = ODCSContract.from_string(
        build_contract(
            property_quality_yaml=_custom_rule(
                f"{module}.value_not_null",
                properties={"column": "email"},
            )
        )
    )

    [test] = resolve_tests(contract)

    assert test.location == "schema[0].properties[0].quality[0]"
