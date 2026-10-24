class ContractError(ValueError):
    """Base class for ODCS contract errors."""


class ContractValidationError(ContractError):
    """The contract is not valid YAML or violates the ODCS schema."""


class UnsupportedODCSVersionError(ContractValidationError):
    """The contract declares an ODCS version DQT does not support."""


class ContractRuleError(ContractError):
    """A contract quality rule cannot be resolved to a DQT test."""
