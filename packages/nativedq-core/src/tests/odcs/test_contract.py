import pytest
from nativedq.odcs import SUPPORTED_ODCS_VERSION, ODCSContract
from nativedq.odcs.errors import (
    ContractValidationError,
    UnsupportedODCSVersionError,
)


def test_loads_valid_contract_and_preserves_standard_fields(build_contract):
    text = build_contract(
        """
        - id: rule_one
          type: custom
          engine: nativedq
          implementation: my_package.quality.rule_one
        """,
        extra_yaml="domain: customers",
    )

    contract = ODCSContract.from_string(text, source="memory")

    assert contract.contract.id == "contract-1"
    assert contract.contract.version == "1.0.0"
    assert contract.contract.kind == "DataContract"
    assert contract.contract.apiVersion == SUPPORTED_ODCS_VERSION
    assert contract.contract.domain == "customers"
    assert contract.source == "memory"


def test_loads_contract_from_a_file(tmp_path, build_contract):
    path = tmp_path / "customers.odcs.yaml"
    path.write_text(
        build_contract("""
            - id: rule_one
              type: custom
              engine: nativedq
              implementation: my_package.quality.rule_one
            """),
        encoding="utf-8",
    )

    contract = ODCSContract.load(path)

    assert contract.source == str(path)
    assert contract.contract.id == "contract-1"


def test_collects_object_and_property_rules_in_document_order(build_contract):
    contract = ODCSContract.from_string(
        build_contract(
            """
            - id: object_rule
              type: custom
              engine: nativedq
              implementation: my_package.quality.object_rule
            """,
            property_quality_yaml="""
            - id: value_rule
              type: custom
              engine: nativedq
              implementation: my_package.quality.value_rule
            """,
        )
    )

    rules = contract.quality_rules()

    assert [rule.location for rule in rules] == [
        "schema[0].quality[0]",
        "schema[0].properties[0].quality[0]",
    ]
    assert [rule.rule.id for rule in rules] == ["object_rule", "value_rule"]
    assert all(rule.schema_name == "customers" for rule in rules)
    assert rules[0].column_name is None
    assert rules[1].column_name == "value"


def test_accepts_a_contract_without_quality_rules(build_contract):
    contract = ODCSContract.from_string(build_contract())

    assert contract.quality_rules() == []


def test_rejects_invalid_yaml():
    with pytest.raises(ContractValidationError, match="not valid YAML"):
        ODCSContract.from_string("version: [1.0.0")


def test_rejects_a_non_mapping_document():
    with pytest.raises(ContractValidationError, match="must be a YAML mapping"):
        ODCSContract.from_string("- one\n- two\n")


def test_rejects_a_contract_missing_required_schema_fields(build_contract):
    text = build_contract().replace("version: 1.0.0\n", "")

    with pytest.raises(ContractValidationError, match="is invalid at"):
        ODCSContract.from_string(text, source="memory")


def test_rejects_unknown_top_level_fields(build_contract):
    text = build_contract(extra_yaml="unknownField: true")

    with pytest.raises(ContractValidationError, match="is invalid at"):
        ODCSContract.from_string(text)


def test_rejects_custom_rule_without_engine_and_implementation(build_contract):
    text = build_contract("""
        - id: broken_rule
          type: custom
        """)

    with pytest.raises(ContractValidationError, match="is invalid at"):
        ODCSContract.from_string(text)


def test_rejects_custom_rule_that_uses_library_arguments(build_contract):
    text = build_contract("""
        - id: broken_rule
          type: custom
          engine: nativedq
          implementation: my_package.quality.rule
          arguments:
            column: value
        """)

    with pytest.raises(ContractValidationError, match="is invalid at"):
        ODCSContract.from_string(text)


def test_rejects_unsupported_odcs_versions(build_contract):
    text = build_contract(api_version="v3.1.0")

    with pytest.raises(
        UnsupportedODCSVersionError,
        match="DQT supports only 'v3.2.0'",
    ):
        ODCSContract.from_string(text)


def test_unknown_odcs_versions_are_reported_as_unsupported(build_contract):
    text = build_contract(api_version="v9.9.9")

    with pytest.raises(
        UnsupportedODCSVersionError,
        match="DQT supports only 'v3.2.0'",
    ):
        ODCSContract.from_string(text)
