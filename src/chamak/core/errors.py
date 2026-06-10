class ChamakError(Exception):
    """Base class for all chamak errors."""


class StorageError(ChamakError):
    pass


class MigrationError(StorageError):
    pass


class GraphError(ChamakError):
    pass


class RuleParseError(ChamakError):
    pass


class RuleEvalError(ChamakError):
    pass


class UnknownMetricError(RuleEvalError):
    pass


class MarketDataError(ChamakError):
    pass


class LLMError(ChamakError):
    pass


class InterviewError(ChamakError):
    pass
