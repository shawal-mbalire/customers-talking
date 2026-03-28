from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class UnifiedSession:
    session_id: str
    phone_number: str
    channel: str  # 'ussd' | 'sms' | 'voice'
    status: str = "active"  # 'active' | 'escalated' | 'resolved'
    last_intent: str = "unknown"
    last_message: str = ""
    agent_reply: str = ""
    reason: str = ""
    messages: list = field(default_factory=list)  # [{role, text, ts}]
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "sessionId": self.session_id,
            "phoneNumber": self.phone_number,
            "channel": self.channel,
            "status": self.status,
            "lastIntent": self.last_intent,
            "lastMessage": self.last_message,
            "agentReply": self.agent_reply,
            "reason": self.reason,
            "messages": self.messages,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


# Keep for backward compatibility
@dataclass
class EscalatedSession:
    session_id: str
    phone_number: str
    last_intent: str
    timestamp: str = field(default_factory=_now)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "sessionId": self.session_id,
            "phoneNumber": self.phone_number,
            "lastIntent": self.last_intent,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


@dataclass
class Solution:
    id: str
    question: str
    answer: str
    intent_name: str = ""
    trigger_phrases: list = field(default_factory=list)
    channels: list = field(default_factory=lambda: ["all"])
    active: bool = True
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "intentName": self.intent_name,
            "triggerPhrases": self.trigger_phrases,
            "channels": self.channels,
            "active": self.active,
            "createdAt": self.created_at,
        }
