import pytest
from nativedq.definitions.dq_test import DQTest

# ---------------------------------------------------------------------------
# DQTest definition
# ---------------------------------------------------------------------------


def test_creates_definition_from_function():
    def test(col: str):
        """Validate a column."""

    dq_test = DQTest(func=test)

    assert dq_test.func is test
    assert dq_test.name == "test"
    assert dq_test.description == "Validate a column."


def test_explicit_metadata_overrides_function_metadata():
    def test(col: str):
        """Function description."""

    dq_test = DQTest(
        func=test,
        name="column_check",
        description="Custom description",
        target_engine="spark",
    )

    assert dq_test.name == "column_check"
    assert dq_test.description == "Custom description"
    assert dq_test.target_engine == "spark"


def test_extracts_test_parameters_from_definition():
    def test(col: str, limit: float):
        pass

    dq_test = DQTest(func=test)

    assert [parameter.name for parameter in dq_test.test_parameters] == [
        "col",
        "limit",
    ]

    assert dq_test.test_parameters[0].annotation is str
    assert dq_test.test_parameters[1].annotation is float


def test_definition_does_not_contain_threshold():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    assert "maximum_accepted_error_percentage" not in dq_test.model_fields


def test_definition_preserves_parameter_defaults():
    def test(col: str, limit: float = 0.05):
        pass

    dq_test = DQTest(func=test)

    assert [
        (parameter.name, parameter.default)
        for parameter in dq_test.test_parameters
    ] == [
        ("col", None),
        ("limit", 0.05),
    ]


def test_definition_supports_keyword_only_parameters():
    def test(col: str, *, case_sensitive: bool = True):
        pass

    dq_test = DQTest(func=test)

    assert [
        parameter.name for parameter in dq_test.test_parameters
    ] == [
        "col",
        "case_sensitive",
    ]

    assert dq_test.test_parameters[1].default is True


# ---------------------------------------------------------------------------
# DQTest call
# ---------------------------------------------------------------------------


def test_call_creates_dq_test_call():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(
        col="age",
        maximum_accepted_error_percentage=80,
    )

    assert call.func_callable is test
    assert len(call.parameters) == 1
    assert call.parameters[0].name == "col"
    assert call.parameters[0].value == "age"
    assert call.maximum_accepted_error_percentage == 80


def test_call_threshold_is_per_invocation():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    strict = dq_test(
        col="age",
        maximum_accepted_error_percentage=5,
    )

    relaxed = dq_test(
        col="age",
        maximum_accepted_error_percentage=80,
    )

    assert strict.maximum_accepted_error_percentage == 5
    assert relaxed.maximum_accepted_error_percentage == 80


def test_call_without_threshold_uses_default():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(col="age")

    assert call.maximum_accepted_error_percentage == 100


def test_call_binds_multiple_test_parameters():
    def test(col: str, limit: float):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(
        col="age",
        limit=0.05,
        maximum_accepted_error_percentage=80,
    )

    assert [
        (parameter.name, parameter.value)
        for parameter in call.parameters
    ] == [
        ("col", "age"),
        ("limit", 0.05),
    ]

    assert call.maximum_accepted_error_percentage == 80


def test_call_rejects_missing_required_parameter():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    with pytest.raises(TypeError):
        dq_test()


def test_call_rejects_unknown_parameter():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    with pytest.raises(TypeError):
        dq_test(
            unknown="age",
            maximum_accepted_error_percentage=80,
        )


def test_call_applies_parameter_defaults():
    def test(col: str, limit: float = 0.05):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(
        col="age",
        maximum_accepted_error_percentage=80,
    )

    assert [
        (parameter.name, parameter.value)
        for parameter in call.parameters
    ] == [
        ("col", "age"),
        ("limit", 0.05),
    ]


def test_call_explicit_parameter_overrides_default():
    def test(col: str, limit: float = 0.05):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(
        col="age",
        limit=0.10,
        maximum_accepted_error_percentage=80,
    )

    assert [
        (parameter.name, parameter.value)
        for parameter in call.parameters
    ] == [
        ("col", "age"),
        ("limit", 0.10),
    ]


def test_call_supports_keyword_only_parameters():
    def test(col: str, *, case_sensitive: bool = True):
        pass

    dq_test = DQTest(func=test)

    call = dq_test(
        col="age",
        case_sensitive=False,
        maximum_accepted_error_percentage=80,
    )

    assert [
        (parameter.name, parameter.value)
        for parameter in call.parameters
    ] == [
        ("col", "age"),
        ("case_sensitive", False),
    ]


def test_call_does_not_mutate_definition():
    def test(col: str):
        pass

    dq_test = DQTest(func=test)

    first = dq_test(
        col="age",
        maximum_accepted_error_percentage=20,
    )

    second = dq_test(
        col="salary",
        maximum_accepted_error_percentage=80,
    )

    assert [
        (parameter.name, parameter.value)
        for parameter in first.parameters
    ] == [
        ("col", "age"),
    ]
    assert first.maximum_accepted_error_percentage == 20

    assert [
        (parameter.name, parameter.value)
        for parameter in second.parameters
    ] == [
        ("col", "salary"),
    ]
    assert second.maximum_accepted_error_percentage == 80

    # The definition itself remains unchanged.
    assert dq_test.name == "test"
    assert dq_test.func is test