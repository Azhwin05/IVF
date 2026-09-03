import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.messaging.models import MessageCategory, MessageChannel, MessageStatus


class MessageTemplateCreate(BaseModel):
    name: str
    channel: MessageChannel
    category: MessageCategory
    body: str


class MessageTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    channel: MessageChannel
    category: MessageCategory
    body: str
    is_active: bool


class CommsPreferenceUpdate(BaseModel):
    promotional_opt_in: bool


class CommsPreferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    patient_id: uuid.UUID
    promotional_opt_in: bool


class SendMessageRequest(BaseModel):
    patient_id: uuid.UUID
    template_id: uuid.UUID | None = None
    body: str | None = None  # required if template_id is not given
    channel: MessageChannel = MessageChannel.WHATSAPP
    category: MessageCategory = MessageCategory.TRANSACTIONAL


class MessageLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    patient_id: uuid.UUID
    channel: MessageChannel
    category: MessageCategory
    body: str
    status: MessageStatus
    provider_message_id: str | None
    failure_reason: str | None
    sent_at: datetime | None
    created_at: datetime
