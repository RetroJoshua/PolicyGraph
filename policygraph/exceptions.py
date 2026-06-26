"""Custom exceptions for PolicyGraph."""


class PolicyGraphError(Exception):
    """Base exception for PolicyGraph."""

    pass


class PolicyParsingError(PolicyGraphError):
    """Raised when policy parsing or validation fails."""

    pass


class ModelLoadingError(PolicyGraphError):
    """Raised when model loading fails."""

    pass


class GraphBuildingError(PolicyGraphError):
    """Raised when graph construction fails."""

    pass


class DatasetError(PolicyGraphError):
    """Raised when dataset loading or processing fails."""

    pass


class TrainingError(PolicyGraphError):
    """Raised when model training fails."""

    pass
