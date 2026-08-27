"""
Structured JSON logging with request-ID correlation.

Never logs: passwords, tokens (access, refresh, or MinIO presigned URLs),
or full patient payloads. Log the fact an action happened and its IDs,
not the sensitive body.
"""
import logging
import sys
import uuid
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

_REDACT_KEYS = {"password", "token", "access_token", "refresh_token", "authorization", "secret"}


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def redact(payload: dict) -> dict:
    """Shallow redaction helper for anything that might get logged incidentally."""
    return {k: ("***REDACTED***" if k.lower() in _REDACT_KEYS else v) for k, v in payload.items()}


def configure_logging(environment: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"
    )
    handler.setFormatter(fmt)
    handler.addFilter(RequestIdFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO if environment == "production" else logging.DEBUG)

    # Quiet the noisy libraries down to warnings
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def new_request_id() -> str:
    return str(uuid.uuid4())
