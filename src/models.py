#src/models.py

from dataclasses import dataclass


@dataclass
class ShipmentState:
    status: str
    status_text: str
    arrival_time: str | None
    last_event_time: str | None