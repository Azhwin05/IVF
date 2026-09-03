"""
Provider abstraction — swap in a real WhatsApp Business API / SMS
gateway client here once one is chosen (NEEDS CLIENT CONFIRMATION, see
models.py docstring) without touching app/messaging/service.py or any
caller. Every provider reads its credentials from environment variables
via app.core.config — never hardcode a credential in this file or
anywhere else, per the source doc's non-negotiable security rule.
"""
import abc
import logging

from app.messaging.models import MessageChannel

logger = logging.getLogger("app.messaging")


class MessageProvider(abc.ABC):
    @abc.abstractmethod
    async def send(self, *, to_phone: str, body: str, channel: MessageChannel) -> tuple[bool, str | None, str | None]:
        """Returns (success, provider_message_id, failure_reason)."""
        raise NotImplementedError


class ConsoleProvider(MessageProvider):
    """The only provider wired up today — deliberately a safe no-op, not
    a real send. Messages are fully logged/auditable (MessageLog rows are
    created regardless of provider) without risking an accidental real
    WhatsApp/SMS send before a provider contract and consent process are
    actually in place. Swap `get_provider()` below once that's decided."""

    async def send(self, *, to_phone: str, body: str, channel: MessageChannel) -> tuple[bool, str | None, str | None]:
        logger.info("messaging.console_provider: would send %s to %s: %s", channel.value, to_phone, body)
        return True, None, None


def get_provider() -> MessageProvider:
    # NEEDS CLIENT CONFIRMATION: branch on settings.MESSAGE_PROVIDER (an
    # env var, never a hardcoded string) once a real provider is chosen —
    # e.g. WhatsAppBusinessProvider(api_key=settings.WHATSAPP_API_KEY).
    return ConsoleProvider()
