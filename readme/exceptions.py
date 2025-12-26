class LLMError(Exception):
    """Base exception for all LLM-related errors."""


class LLMConfigurationError(LLMError):
    """Raised when LLM is misconfigured (missing keys, bad config)."""


class LLMRateLimitError(LLMError):
    """Raised when the LLM provider rate-limits requests."""


class LLMTemporaryError(LLMError):
    """Raised for transient errors that are retryable."""


class LLMFatalError(LLMError):
    """Raised for non-retryable LLM failures."""
    
class LLMGenerationError(Exception):
    """Raised when the LLM fails to generate or enhance README content."""
    pass

