class LlmError(Exception):
    pass


class LlmNotConfigured(LlmError):
    pass


class LlmTimeout(LlmError):
    pass


class LlmFailed(LlmError):
    pass
