#tests/test_tracker_errors.py

from src.models import ShipmentState
from src.tracker import Tracker


class FakeClient:
    tracking_number = "1234567890"
    postal_code = "1234"

    def __init__(self):
        self.call_count = 0

    def get_shipment(self) -> ShipmentState:
        self.call_count += 1

        if self.call_count == 1:
            raise RuntimeError(
                "Test GLS API error"
            )

        if self.call_count == 2:
            return ShipmentState(
                status="INDELIVERY",
                status_text="GLS vehicle, out for delivery",
                arrival_time="16:00-19:00",
                last_event_time="2026-10-07",
            )

        return ShipmentState(
            status="DELIVERED",
            status_text="Delivered",
            arrival_time=None,
            last_event_time="2026-10-07",
        )


def test_tracker_recovers_after_api_error() -> None:
    client = FakeClient()

    tracker = Tracker(
        client=client,
        min_polling=1,
        max_polling=1,
        randomize=False,
        sound_enabled=False,
        persist_state=False,
    )

    try:
        client.get_shipment()

    except RuntimeError as exc:
        assert str(exc) == "Test GLS API error"

    state = client.get_shipment()

    assert state.status == "INDELIVERY"

    should_stop = tracker._process_state(state)

    assert should_stop is False

    state = client.get_shipment()

    should_stop = tracker._process_state(state)

    assert should_stop is True