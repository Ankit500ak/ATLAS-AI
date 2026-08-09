class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AIServiceError(AppException):
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, status_code=503)


class FinancialDataError(AppException):
    def __init__(self, message: str = "Financial data unavailable"):
        super().__init__(message, status_code=503)


class DocumentProcessingError(AppException):
    def __init__(self, message: str = "Document processing failed"):
        super().__init__(message, status_code=422)


class UserNotFoundError(AppException):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, status_code=404)


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)
