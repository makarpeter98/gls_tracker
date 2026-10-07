#src/state_store.py

import json
from pathlib import Path

from .models import ShipmentState


DATA_DIR = Path("data")
STATE_FILE = DATA_DIR / "last_state.json"


def load_state(
    tracking_number: str,
    postal_code: str,
) -> ShipmentState | None:
    if not STATE_FILE.exists():
        return None

    try:
        with STATE_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (OSError, json.JSONDecodeError):
        return None

    if data.get("tracking_number") != tracking_number:
        return None

    if data.get("postal_code") != postal_code:
        return None

    state_data = data.get("state")

    if not isinstance(state_data, dict):
        return None

    return ShipmentState(
        status=state_data.get("status", ""),
        status_text=state_data.get("status_text", ""),
        arrival_time=state_data.get("arrival_time"),
        last_event_time=state_data.get("last_event_time"),
        eta=_parse_datetime(
            state_data.get("eta")
        ),
        eta_min=_parse_datetime(
            state_data.get("eta_min")
        ),
        eta_max=_parse_datetime(
            state_data.get("eta_max")
        ),
        remaining_stops=state_data.get(
            "remaining_stops"
        ),
        position_lat=state_data.get(
            "position_lat"
        ),
        position_lng=state_data.get(
            "position_lng"
        ),
    )


def save_state(
    tracking_number: str,
    postal_code: str,
    state: ShipmentState,
) -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "tracking_number": tracking_number,
        "postal_code": postal_code,
        "state": {
            "status": state.status,
            "status_text": state.status_text,
            "arrival_time": state.arrival_time,
            "last_event_time": state.last_event_time,
            "eta": _format_datetime(state.eta),
            "eta_min": _format_datetime(state.eta_min),
            "eta_max": _format_datetime(state.eta_max),
            "remaining_stops": state.remaining_stops,
            "position_lat": state.position_lat,
            "position_lng": state.position_lng,
        },
    }

    with STATE_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )


def _format_datetime(value) -> str | None:
    if value is None:
        return None

    return value.isoformat()


def _parse_datetime(value):
    if not value:
        return None

    try:
        from datetime import datetime

        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    except (
        TypeError,
        ValueError,
    ):
        return None