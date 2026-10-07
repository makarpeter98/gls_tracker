#tests/test_tracker.py

from src.models import ShipmentState
from src.tracker import Tracker


class FakeClient:
    tracking_number = "1234567890"
    postal_code = "1234"


def test_tracker_state_changes_and_delivery() -> None:
    tracker = Tracker(
        client=FakeClient(),
        min_polling=1,
        max_polling=1,
        randomize=False,
        sound_enabled=False,
        persist_state=False,
    )

    initial_state = ShipmentState(
        status="INDELIVERY",
        status_text="GLS vehicle, out for delivery",
        arrival_time="16:00-19:00",
        last_event_time="2026-10-07",
    )

    changed_state = ShipmentState(
        status="INDELIVERY",
        status_text="GLS vehicle, out for delivery",
        arrival_time="17:00-20:00",
        last_event_time="2026-10-07",
    )

    delivered_state = ShipmentState(
        status="DELIVERED",
        status_text="Delivered",
        arrival_time=None,
        last_event_time="2026-10-07",
    )

    assert tracker._process_state(initial_state) is False

    changes = tracker._detect_changes(
        initial_state,
        changed_state,
    )

    assert len(changes) == 1
    assert "Expected delivery:" in changes[0]

    assert tracker._process_state(changed_state) is False

    assert tracker._process_state(delivered_state) is True