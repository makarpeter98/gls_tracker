#src/models.py

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ShipmentState:
    status: str
    status_text: str
    arrival_time: str | None
    last_event_time: str | None

    eta: datetime | None = None
    eta_min: datetime | None = None
    eta_max: datetime | None = None
    remaining_stops: int | None = None
    position_lat: float | None = None
    position_lng: float | None = None


@dataclass
class LiveTrackingState:
    eta: datetime | None
    eta_min: datetime | None
    eta_max: datetime | None
    remaining_stops: int | None
    position_lat: float | None
    position_lng: float | None