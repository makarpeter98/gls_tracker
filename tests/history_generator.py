#tests/history_generator.py

import json
from pathlib import Path


TRACKING_NUMBER = "3422719707"
POSTAL_CODE = "4028"

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_FILE = BASE_DIR / "data" / "history.json"


events = [
    ("2026-10-07T12:35:35+02:00", 50, 48),
    ("2026-10-07T12:37:27+02:00", 48, 46),
    ("2026-10-07T12:47:03+02:00", 46, 45),
    ("2026-10-07T13:00:24+02:00", 45, 44),
    ("2026-10-07T13:06:44+02:00", 44, 43),
    ("2026-10-07T13:13:07+02:00", 43, 42),
    ("2026-10-07T13:20:53+02:00", 42, 41),
    ("2026-10-07T13:26:02+02:00", 41, 40),
    ("2026-10-07T13:30:16+02:00", 40, 39),
    ("2026-10-07T13:40:48+02:00", 39, 38),
    ("2026-10-07T13:48:50+02:00", 38, 36),
    ("2026-10-07T14:00:56+02:00", 36, 34),
    ("2026-10-07T14:10:14+02:00", 34, 31),
    ("2026-10-07T14:17:26+02:00", 31, 29),
    ("2026-10-07T14:25:25+02:00", 29, 27),
    ("2026-10-07T14:33:09+02:00", 27, 25),
    ("2026-10-07T14:39:06+02:00", 25, 23),
    ("2026-10-07T14:50:46+02:00", 23, 21),
    ("2026-10-07T14:56:25+02:00", 21, 19),
    ("2026-10-07T15:04:34+02:00", 19, 18),
    ("2026-10-07T15:13:43+02:00", 18, 16),
]


def parse_timestamp(value: str):
    from datetime import datetime

    return datetime.fromisoformat(value)


history = []

previous_timestamp = None

for timestamp_text, previous_stops, current_stops in events:
    timestamp = parse_timestamp(timestamp_text)

    if previous_timestamp is None:
        # Az első esemény előtt nem tudjuk,
        # mennyi idő telt el az előző stop óta.
        previous_timestamp = timestamp
        continue

    elapsed_seconds = (
        timestamp - previous_timestamp
    ).total_seconds()

    stop_count = previous_stops - current_stops

    if stop_count <= 0:
        previous_timestamp = timestamp
        continue

    seconds_per_stop = (
        elapsed_seconds / stop_count
    )

    for offset in range(stop_count):
        stop_before = previous_stops - offset
        stop_after = stop_before - 1

        history.append(
            {
                "previous_stops": stop_before,
                "stop": stop_after,
                "timestamp": timestamp_text,
                "duration_seconds": round(
                    seconds_per_stop,
                    1,
                ),
            }
        )

    previous_timestamp = timestamp


OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True,
)

data = {
    "tracking_number": TRACKING_NUMBER,
    "postal_code": POSTAL_CODE,
    "history": history,
}

OUTPUT_FILE.write_text(
    json.dumps(
        data,
        ensure_ascii=False,
        indent=4,
    ),
    encoding="utf-8",
)

print(f"History generated: {OUTPUT_FILE}")
print(f"Entries: {len(history)}")