from importlib import import_module
from inspect import Parameter, signature
from typing import Any, Dict, List

from pydantic import Field

from dqt.definitions import DQTest
from dqt.odcs.contract import ContractQualityRule, ODCSContract
from dqt.odcs.errors import ContractRuleError

DQT_ENGINE = "dqt"
MAXIMUM_ACCEPTED_ERROR_PROPERTY = "maximum_accepted_error_percentage"


class ContractDQTest(DQTest):
    """A DQT test selected by an ODCS quality rule.

    Executors call ``test()`` without arguments. The contract-supplied
    arguments and threshold are therefore carried by the definition so the
    existing execution pipeline can evaluate the rule unchanged.
    """

    contract_rule_id: str
    implementation: str
    location: str

    contract_rule_description: str | None = None
    severity: str | None = None
    dimension: str | None = None

    arguments: Dict[str, Any] = Field(default_factory=dict)
    maximum_accepted_error_percentage: float = 100.0

    def __call__(
        self,
        *args: Any,
        maximum_accepted_error_percentage: float | None = None,
        **kwargs: Any,
    ):
        if maximum_accepted_error_percentage is None:
            maximum_accepted_error_percentage = self.maximum_accepted_error_percentage

        return super().__call__(
            *args,
            maximum_accepted_error_percentage=maximum_accepted_error_percentage,
            **{**self.arguments, **kwargs},
        )


def resolve_tests(contract: ODCSContract) -> List[ContractDQTest]:
    """Resolve every ODCS quality rule to a ``@dq_test`` definition.

    All problems are reported together. A rule that cannot be executed is
    never silently dropped.
    """

    resolved: List[ContractDQTest] = []
    errors: List[str] = []
    seen_ids: Dict[str, str] = {}

    for quality_rule in contract.quality_rules():
        rule = quality_rule.rule

        if rule.id:
            previous_location = seen_ids.get(rule.id)

            if previous_location is not None:
                errors.append(
                    f"{quality_rule.location}: duplicate quality rule id "
                    f"{rule.id!r}, already declared at {previous_location}"
                )
                continue

            seen_ids[rule.id] = quality_rule.location

        try:
            resolved.append(_resolve_rule(quality_rule))
        except ContractRuleError as exc:
            errors.append(str(exc))

    if errors:
        source = f" {contract.source!r}" if contract.source else ""
        details = "\n".join(f"- {error}" for error in errors)
        raise ContractRuleError(
            f"ODCS contract{source} contains quality rules DQT cannot "
            f"execute:\n{details}"
        )

    return resolved


def _resolve_rule(quality_rule: ContractQualityRule) -> ContractDQTest:
    rule = quality_rule.rule
    location = quality_rule.location

    if not rule.id:
        raise ContractRuleError(
            f"{location}: executable quality rule is missing the mandatory "
            "'id' field"
        )

    rule_id = rule.id

    if rule.type != "custom":
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} has type "
            f"{rule.type or 'library'!r}; DQT executes only 'custom' rules "
            f"with engine {DQT_ENGINE!r}"
        )

    if rule.engine != DQT_ENGINE:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} declares engine "
            f"{rule.engine!r}; DQT executes only engine {DQT_ENGINE!r}"
        )

    implementation = rule.implementation

    if not isinstance(implementation, str) or not implementation:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} requires 'implementation' "
            "to be a dotted Python import path such as "
            "'my_package.quality.my_test'"
        )

    test = _import_test(implementation, location, rule_id)
    arguments, threshold = _read_execution_properties(quality_rule, test)

    return ContractDQTest(
        func=test.func,
        name=test.name,
        description=test.description,
        target_engine=test.target_engine,
        contract_rule_id=rule_id,
        implementation=implementation,
        location=location,
        contract_rule_description=rule.description,
        severity=rule.severity,
        dimension=rule.dimension,
        arguments=arguments,
        maximum_accepted_error_percentage=threshold,
    )


def _import_test(
    implementation: str,
    location: str,
    rule_id: str,
) -> DQTest:
    module_name, _, attribute_name = implementation.rpartition(".")

    if not module_name or not attribute_name:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} implementation "
            f"{implementation!r} is not a dotted import path "
            "('package.module.attribute')"
        )

    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} cannot import module "
            f"{module_name!r} from implementation {implementation!r}: {exc}"
        ) from exc
    except ImportError as exc:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} failed to import "
            f"{module_name!r} from implementation {implementation!r}: {exc}"
        ) from exc

    try:
        target = getattr(module, attribute_name)
    except AttributeError as exc:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} implementation "
            f"{implementation!r} does not exist: module {module_name!r} has "
            f"no attribute {attribute_name!r}"
        ) from exc

    if not isinstance(target, DQTest):
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} implementation "
            f"{implementation!r} resolved to {type(target).__name__}, not a "
            "function decorated with @dq_test"
        )

    return target


def _read_execution_properties(
    quality_rule: ContractQualityRule,
    test: DQTest,
) -> tuple[Dict[str, Any], float]:
    rule = quality_rule.rule
    location = quality_rule.location

    arguments: Dict[str, Any] = {}
    threshold = 100.0
    threshold_declared = False

    for custom_property in rule.customProperties or []:
        name = custom_property.property

        if not name:
            raise ContractRuleError(
                f"{location}: quality rule {rule.id!r} has a customProperties "
                "entry without a 'property' name"
            )

        if name == MAXIMUM_ACCEPTED_ERROR_PROPERTY:
            if threshold_declared:
                raise ContractRuleError(
                    f"{location}: quality rule {rule.id!r} declares custom "
                    f"property {name!r} more than once"
                )

            threshold_declared = True
            threshold = _read_threshold(
                custom_property.value,
                location,
                rule.id,
            )
            continue

        if name in arguments:
            raise ContractRuleError(
                f"{location}: quality rule {rule.id!r} declares custom "
                f"property {name!r} more than once"
            )

        arguments[name] = custom_property.value

    _validate_arguments(test, arguments, location, rule.id)

    return arguments, threshold


def _read_threshold(
    value: Any,
    location: str,
    rule_id: str,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} custom property "
            f"{MAXIMUM_ACCEPTED_ERROR_PROPERTY!r} must be a number between 0 "
            f"and 100, got {value!r}"
        )

    if not 0 <= value <= 100:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} custom property "
            f"{MAXIMUM_ACCEPTED_ERROR_PROPERTY!r} must be between 0 and 100, "
            f"got {value!r}"
        )

    return float(value)


def _validate_arguments(
    test: DQTest,
    arguments: Dict[str, Any],
    location: str,
    rule_id: str,
) -> None:
    parameters = signature(test.func).parameters

    unknown = sorted(name for name in arguments if name not in parameters)

    if unknown:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} provides custom properties "
            f"{unknown} that are not parameters of {test.name!r}. Expected "
            f"parameters: {sorted(parameters)}"
        )

    positional_only = sorted(
        name for name in arguments if parameters[name].kind is Parameter.POSITIONAL_ONLY
    )

    if positional_only:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} cannot pass "
            f"{positional_only} by name because {test.name!r} declares them "
            "as positional-only"
        )

    missing = sorted(
        name
        for name, parameter in parameters.items()
        if parameter.default is Parameter.empty
        and parameter.kind
        in (
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.KEYWORD_ONLY,
        )
        and name not in arguments
    )

    if missing:
        raise ContractRuleError(
            f"{location}: quality rule {rule_id!r} is missing required "
            f"parameters {missing} for {test.name!r}; provide them as "
            "ODCS customProperties"
        )
