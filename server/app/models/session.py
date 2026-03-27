from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EscalatedSession:
    session_id: str
    phone_number: str
    last_intent: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "sessionId": self.session_id,
            "phoneNumber": self.phone_number,
            "lastIntent": self.last_intent,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }
