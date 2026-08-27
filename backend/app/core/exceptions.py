"""
Domain-level exceptions, mapped to consistent HTTP responses in main.py.
Using explicit typed exceptions instead of raising HTTPException everywhere
keeps business logic decoupled from the web layer (services stay testable
without FastAPI in the loop).
"""


class DomainError(Exception):
    """Base class for all business-rule violations."""
    status_code = 400
    error_code = "domain_error"

    def __init__(self, message: str, *, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        if error_code:
            self.error_code = error_code


class NotFoundError(DomainError):
    status_code = 404
    error_code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    error_code = "conflict"


class ValidationFailedError(DomainError):
    status_code = 422
    error_code = "validation_failed"


class PermissionDeniedError(DomainError):
    status_code = 403
    error_code = "permission_denied"


class AuthenticationError(DomainError):
    status_code = 401
    error_code = "authentication_failed"


class InsufficientStockError(DomainError):
    status_code = 409
    error_code = "insufficient_stock"


class PaymentRequiredError(DomainError):
    status_code = 402
    error_code = "payment_required"


class IdempotencyConflictError(DomainError):
    """Raised when a request with a previously-seen idempotency key arrives
    with a different payload than the original — prevents silent data drift."""
    status_code = 409
    error_code = "idempotency_conflict"


class RateLimitedError(DomainError):
    status_code = 429
    error_code = "rate_limited"
