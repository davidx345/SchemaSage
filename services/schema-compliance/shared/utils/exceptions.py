"""Custom exceptions for SchemaSage."""

class SchemaSageException(Exception):
    """Base exception for SchemaSage."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SchemaSageException):
    """Validation error."""
    
    def __init__(self, message: str, field: str = None, details: dict = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundError(SchemaSageException):
    """Resource not found error."""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND", {"resource": resource, "identifier": identifier})


class AuthenticationError(SchemaSageException):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(SchemaSageException):
    """Authorization error."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHORIZATION_ERROR")


class ProcessingError(SchemaSageException):
    """File processing error."""
    
    def __init__(self, message: str, file_type: str = None, details: dict = None):
        error_details = details or {}
        if file_type:
            error_details["file_type"] = file_type
        super().__init__(message, "PROCESSING_ERROR", error_details)


class ServiceUnavailableError(SchemaSageException):
    """Service unavailable error."""
    
    def __init__(self, service_name: str, message: str = None):
        msg = message or f"Service {service_name} is unavailable"
        super().__init__(msg, "SERVICE_UNAVAILABLE", {"service": service_name})
