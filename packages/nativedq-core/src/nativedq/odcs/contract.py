import json
from importlib import resources
from pathlib import Path
from typing import Any, List

import jsonschema
import yaml
from open_data_contract_standard.model import (
    DataQuality,
    OpenDataContractStandard,
)
from pydantic import BaseModel, ValidationError

from nativedq.odcs.errors import (
    ContractValidationError,
    UnsupportedODCSVersionError,
)

# DQT validates against the schema bundled with the installed
# open-data-contract-standard package, so one ODCS version is supported at a
# time. To enable a newer version: install the matching
# open-data-contract-standard release, add its apiVersion below, and extend the
# contract tests and docs (`docs/reference/odcs.md`).
SUPPORTED_ODCS_VERSION = "v3.2.0"
_SUPPORTED_ODCS_VERSIONS = (SUPPORTED_ODCS_VERSION,)


class ContractQualityRule(BaseModel):
    """An ODCS quality rule and the contract location it was declared in."""

    rule: DataQuality
    location: str
    schema_name: str | None = None
    column_name: str | None = None


def _odcs_schema() -> dict[str, Any]:
    schema_file = resources.files("open_data_contract_standard").joinpath("schema.json")

    return json.loads(schema_file.read_text(encoding="utf-8"))


def _validate_document(document: Any, source: str | None) -> None:
    api_version = document.get("apiVersion")

    if api_version not in _SUPPORTED_ODCS_VERSIONS:
        supported = ", ".join(repr(version) for version in _SUPPORTED_ODCS_VERSIONS)
        raise UnsupportedODCSVersionError(
            f"ODCS contract{_describe_source(source)} declares apiVersion "
            f"{api_version!r}; DQT supports only {supported}"
        )

    try:
        jsonschema.validate(instance=document, schema=_odcs_schema())
    except jsonschema.ValidationError as exc:
        raise ContractValidationError(
            f"ODCS contract{_describe_source(source)} is invalid at "
            f"{exc.json_path}: {exc.message}"
        ) from exc


def _describe_source(source: str | None) -> str:
    return f" {source!r}" if source else ""


class ODCSContract(BaseModel):
    """A structurally validated ODCS v3.2.0 contract."""

    contract: OpenDataContractStandard
    source: str | None = None

    @classmethod
    def load(cls, path: str | Path) -> "ODCSContract":
        path = Path(path)

        return cls.from_string(
            path.read_text(encoding="utf-8"),
            source=str(path),
        )

    @classmethod
    def from_string(
        cls,
        text: str,
        source: str | None = None,
    ) -> "ODCSContract":
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ContractValidationError(
                f"ODCS contract{_describe_source(source)} is not valid YAML: {exc}"
            ) from exc

        if not isinstance(document, dict):
            raise ContractValidationError(
                f"ODCS contract{_describe_source(source)} must be a YAML "
                "mapping at the top level"
            )

        _validate_document(document, source)

        try:
            contract = OpenDataContractStandard.model_validate(document)
        except ValidationError as exc:
            raise ContractValidationError(
                f"ODCS contract{_describe_source(source)} cannot be mapped to "
                f"the ODCS model: {exc}"
            ) from exc

        return cls(contract=contract, source=source)

    def quality_rules(self) -> List[ContractQualityRule]:
        """Return every quality rule in document order.

        ODCS v3.2.0 declares quality rules on schema objects and on their
        properties. Object-level rules come before property-level rules.
        """

        rules: List[ContractQualityRule] = []

        for schema_index, schema in enumerate(self.contract.schema_ or []):
            for rule_index, rule in enumerate(schema.quality or []):
                rules.append(
                    ContractQualityRule(
                        rule=rule,
                        location=f"schema[{schema_index}].quality[{rule_index}]",
                        schema_name=schema.name,
                    )
                )

            for property_index, schema_property in enumerate(schema.properties or []):
                for rule_index, rule in enumerate(schema_property.quality or []):
                    rules.append(
                        ContractQualityRule(
                            rule=rule,
                            location=(
                                f"schema[{schema_index}].properties"
                                f"[{property_index}].quality[{rule_index}]"
                            ),
                            schema_name=schema.name,
                            column_name=schema_property.name,
                        )
                    )

        return rules
