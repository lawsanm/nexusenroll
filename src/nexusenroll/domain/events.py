"""Domain events -- the payload carried by the Observer pattern (pattern 4).

At architecture scale these are the topics on the Message Broker (diagram 01).
At class scale they are what NotificationPublisher dispatches.  They are the
same idea at two scales, which is the point made in 00-architecture-decision.md
section A2.5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import EventType


@dataclass(frozen=True)
class DomainEvent:
    """Immutable fact: something happened.

    The publisher knows only this; it has no idea who consumes it.  That is
    exactly what the requirement means by "decoupled from the core enrolment
    logic".
    """

    event_type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        return self.payload.get(key, default)

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{self.event_type.value}({self.payload})"
