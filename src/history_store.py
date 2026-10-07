#src/history_store.py

import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path("data")
HISTORY_FILE = DATA_DIR / "history.json"

MAX_HISTORY_ENTRIES = 5000


def load_history(
    tracking_number: str,
    postal_code: str,
) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []

    try:
        with HISTORY_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except (OSError, json.JSONDecodeError):
        return []

    if (
        data.get("tracking_number") != tracking_number
        or data.get("postal_code") != postal_code
    ):
        return []

    history = data.get("history", [])

    if not isinstance(history, list):
        return []

    return history


def append_stop_history(
    tracking_number: str,
    postal_code: str,
    *,
    previous_stops: int,
    current_stops: int,
    timestamp: datetime,
    duration_seconds: float,
) -> list[dict]:
    history = load_history(
        tracking_number=tracking_number,
        postal_code=postal_code,
    )

    entry = {
        "previous_stops": previous_stops,
        "stop": current_stops,
        "timestamp": timestamp.isoformat(),
        "duration_seconds": round(
            duration_seconds,
            1,
        ),
    }

    history.append(entry)

    if len(history) > MAX_HISTORY_ENTRIES:
        history = history[-MAX_HISTORY_ENTRIES:]

    _save_history(
        tracking_number=tracking_number,
        postal_code=postal_code,
        history=history,
    )

    return history


def _save_history(
    tracking_number: str,
    postal_code: str,
    history: list[dict],
) -> None:
    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "tracking_number": tracking_number,
        "postal_code": postal_code,
        "history": history,
    }

    with HISTORY_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4,
        )