"""
Custom Exceptions for Text Morph
Defines all custom exception classes used throughout the application
"""


class TextMorphError(Exception):
    """Base exception class for all Text Morph errors."""
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize TextMorphError.
        
        Args:
            message: Error message
            details: Additional error details
        """
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class ConfigurationError(TextMorphError):
    """Raised when there's an error in configuration."""
    
    def __init__(self, message: str, config_key: str = None):
        """
        Initialize ConfigurationError.
        
        Args:
            message: Error message
            config_key: The configuration key that caused the error
        """
        self.config_key = config_key
        details = f"Config key: {config_key}" if config_key else None
        super().__init__(message, details)


class APIError(TextMorphError):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, status_code: int = None, response: str = None):
        """
        Initialize APIError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response: API response text
        """
        self.status_code = status_code
        self.response = response
        details = f"Status: {status_code}, Response: {response}" if status_code else None
        super().__init__(message, details)


class HuggingFaceAPIError(APIError):
    """Raised when Hugging Face API encounters an error."""
    
    def __init__(self, message: str = "Hugging Face API error", status_code: int = None, response: str = None):
        super().__init__(message, status_code, response)


class GROQAPIError(APIError):
    """Raised when GROQ API encounters an error."""
    
    def __init__(self, message: str = "GROQ API error", status_code: int = None, response: str = None):
        super().__init__(message, status_code, response)


class APIKeyError(TextMorphError):
    """Raised when API key is missing or invalid."""
    
    def __init__(self, service: str):
        """
        Initialize APIKeyError.
        
        Args:
            service: The service name (e.g., 'Hugging Face', 'GROQ')
        """
        self.service = service
        message = f"API key for {service} is missing or invalid"
        super().__init__(message)


class APITimeoutError(APIError):
    """Raised when API request times out."""
    
    def __init__(self, service: str, timeout: int):
        """
        Initialize APITimeoutError.
        
        Args:
            service: The service name
            timeout: Timeout duration in seconds
        """
        self.service = service
        self.timeout = timeout
        message = f"{service} API request timed out after {timeout} seconds"
        super().__init__(message)


class ModelLoadingError(APIError):
    """Raised when AI model is loading or unavailable."""
    
    def __init__(self, model_name: str):
        """
        Initialize ModelLoadingError.
        
        Args:
            model_name: Name of the model being loaded
        """
        self.model_name = model_name
        message = f"Model '{model_name}' is currently loading. Please try again in a few moments."
        super().__init__(message, status_code=503)


class InputValidationError(TextMorphError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, input_type: str = None):
        """
        Initialize InputValidationError.
        
        Args:
            message: Error message
            input_type: Type of input that failed validation
        """
        self.input_type = input_type
        details = f"Input type: {input_type}" if input_type else None
        super().__init__(message, details)


class TextTooLongError(InputValidationError):
    """Raised when input text exceeds maximum length."""
    
    def __init__(self, current_length: int, max_length: int):
        """
        Initialize TextTooLongError.
        
        Args:
            current_length: Current text length
            max_length: Maximum allowed length
        """
        self.current_length = current_length
        self.max_length = max_length
        message = f"Text is too long ({current_length} chars). Maximum allowed: {max_length} characters."
        super().__init__(message, input_type="text_length")


class TextTooShortError(InputValidationError):
    """Raised when input text is below minimum length."""
    
    def __init__(self, current_length: int, min_length: int):
        """
        Initialize TextTooShortError.
        
        Args:
            current_length: Current text length
            min_length: Minimum required length
        """
        self.current_length = current_length
        self.min_length = min_length
        message = f"Text is too short ({current_length} chars). Minimum required: {min_length} characters."
        super().__init__(message, input_type="text_length")


class EmptyInputError(InputValidationError):
    """Raised when input text is empty."""
    
    def __init__(self):
        message = "No text provided. Please enter some text to process."
        super().__init__(message, input_type="empty_text")


class SummarizationError(TextMorphError):
    """Raised when summarization process fails."""
    
    def __init__(self, message: str, method: str = None):
        """
        Initialize SummarizationError.
        
        Args:
            message: Error message
            method: Summarization method ('extractive' or 'abstractive')
        """
        self.method = method
        details = f"Method: {method}" if method else None
        super().__init__(message, details)


class ParaphrasingError(TextMorphError):
    """Raised when paraphrasing process fails."""
    
    def __init__(self, message: str):
        super().__init__(message)


class PipelineError(TextMorphError):
    """Raised when pipeline initialization or execution fails."""
    
    def __init__(self, message: str, component: str = None):
        """
        Initialize PipelineError.
        
        Args:
            message: Error message
            component: Pipeline component that failed
        """
        self.component = component
        details = f"Component: {component}" if component else None
        super().__init__(message, details)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    
    def __init__(self, service: str, retry_after: int = None):
        """
        Initialize RateLimitError.
        
        Args:
            service: The service name
            retry_after: Seconds to wait before retrying
        """
        self.service = service
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f". Please retry after {retry_after} seconds."
        super().__init__(message, status_code=429)


class NetworkError(TextMorphError):
    """Raised when network-related errors occur."""
    
    def __init__(self, message: str = "Network error occurred"):
        super().__init__(message)


class FileOperationError(TextMorphError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, filepath: str = None):
        """
        Initialize FileOperationError.
        
        Args:
            message: Error message
            filepath: Path to the file that caused the error
        """
        self.filepath = filepath
        details = f"File: {filepath}" if filepath else None
        super().__init__(message, details)


class LoggingError(TextMorphError):
    """Raised when logging setup or operation fails."""
    
    def __init__(self, message: str):
        super().__init__(message)


# Error code mapping for standardized error handling
ERROR_CODES = {
    ConfigurationError: "CONFIG_ERROR",
    APIKeyError: "API_KEY_ERROR",
    HuggingFaceAPIError: "HF_API_ERROR",
    GROQAPIError: "GROQ_API_ERROR",
    APITimeoutError: "API_TIMEOUT",
    ModelLoadingError: "MODEL_LOADING",
    TextTooLongError: "TEXT_TOO_LONG",
    TextTooShortError: "TEXT_TOO_SHORT",
    EmptyInputError: "EMPTY_INPUT",
    SummarizationError: "SUMMARIZATION_ERROR",
    ParaphrasingError: "PARAPHRASING_ERROR",
    PipelineError: "PIPELINE_ERROR",
    RateLimitError: "RATE_LIMIT_ERROR",
    NetworkError: "NETWORK_ERROR",
    FileOperationError: "FILE_ERROR",
    LoggingError: "LOGGING_ERROR",
}


def get_error_code(exception: Exception) -> str:
    """
    Get standardized error code for an exception.
    
    Args:
        exception: The exception instance
        
    Returns:
        Error code string
    """
    return ERROR_CODES.get(type(exception), "UNKNOWN_ERROR")


def format_error_for_ui(exception: Exception) -> str:
    """
    Format exception for user-friendly display in UI.
    
    Args:
        exception: The exception to format
        
    Returns:
        Formatted error message string
    """
    if isinstance(exception, TextMorphError):
        return f"❌ {exception.message}"
    return f"❌ An error occurred: {str(exception)}"


if __name__ == "__main__":
    # Test exceptions
    try:
        raise HuggingFaceAPIError("Test error", status_code=503)
    except HuggingFaceAPIError as e:
        print(f"Caught: {e}")
        print(f"Error Code: {get_error_code(e)}")
        print(f"UI Format: {format_error_for_ui(e)}")
    
    try:
        raise TextTooLongError(15000, 10000)
    except TextTooLongError as e:
        print(f"\nCaught: {e}")
        print(f"Error Code: {get_error_code(e)}")
        print(f"UI Format: {format_error_for_ui(e)}")