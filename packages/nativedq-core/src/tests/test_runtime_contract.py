import pytest
from nativedq.decorators import dq_test
from nativedq.definitions import DQTest

def _positive_rule(value: int) -> bool:
    """Value must be positive."""
    return value > 0


def test_nativedqest_uses_function_name_and_docstring_by_default():
    test = DQTest(func=_positive_rule)

    assert test.name == "_positive_rule"
    assert test.description == "Value must be positive."
    assert test.target_engine is None


def test_nativedqest_without_docstring_has_none_description():
    def no_doc(value: int) -> bool:
        return value > 0

    test = DQTest(func=no_doc)

    assert test.name == "no_doc"
    assert test.description is None


def test_nativedqest_binds_parameters_and_requires_valid_kwargs():
    test = DQTest(func=_positive_rule)

    call = test(value=7)
    assert [
        (parameter.name, parameter.value) for parameter in call.parameters
    ] == [("value", 7)]
    assert call.maximum_accepted_error_percentage == 100

    with pytest.raises(TypeError):
        test()

    with pytest.raises(TypeError):
        test(value=7, extra=3)


def test_nativedqest_decorator_wraps_metadata_and_parameter_contract():
    @dq_test(name="is_positive", description="value must be positive", target_engine="spark")
    def custom_rule(value: int, threshold: int = 0) -> bool:
        return value > threshold

    assert custom_rule.name == "is_positive"
    assert custom_rule.description == "value must be positive"
    assert custom_rule.target_engine == "spark"
    parameters = {
        parameter.name: parameter
        for parameter in custom_rule.test_parameters
    }
    assert list(parameters) == ["value", "threshold"]
    assert parameters["value"].name == "value"
    assert parameters["value"].annotation is int
    assert parameters["threshold"].name == "threshold"
    assert parameters["threshold"].annotation is int

    call = custom_rule(value=3, threshold=1)
    assert [
        (parameter.name, parameter.value) for parameter in call.parameters
    ] == [("value", 3), ("threshold", 1)]


def test_nativedqest_call_keeps_zero_threshold_values():
    test = DQTest(func=_positive_rule)

    call = test(value=7, maximum_accepted_error_percentage=0.0)

    assert call.maximum_accepted_error_percentage == 0.0


def test_nativedqest_decorator_supports_plain_usage_without_parentheses():
    @dq_test
    def plain_rule(value: int) -> bool:
        """Plain rule."""
        return value > 0

    assert isinstance(plain_rule, DQTest)
    assert plain_rule.name == "plain_rule"
    assert plain_rule.description == "Plain rule."
    assert plain_rule.func is not None