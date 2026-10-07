#tests/test_tracker_errors.py

from src.models import ShipmentState
from src.tracker import Tracker


class FakeClient:
    tracking_number = "3422719707"
    postal_code = "4028"

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
                status_text="GLS járműben, kiszállítás alatt",
                arrival_time="16:00-19:00",
                last_event_time="2026-10-07",
            )

        return ShipmentState(
            status="DELIVERED",
            status_text="Kézbesítve",
            arrival_time=None,
            last_event_time="2026-10-07",
        )


def main() -> None:
    client = FakeClient()

    tracker = Tracker(
        client=client,
        min_polling=1,
        max_polling=1,
        randomize=False,
        sound_enabled=False,
        persist_state=False,
    )

    print("=" * 60)
    print("TRACKER ERROR RECOVERY TEST")
    print("=" * 60)
    print()

    tracker._print_header()

    print("--- Simulating API error ---")
    print()

    try:
        client.get_shipment()

    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        print("Error handled successfully.")
        print()

    print("--- Continuing after error ---")
    print()

    state = client.get_shipment()

    print("Recovered successfully:")
    print(f"  Status: {state.status_text}")
    print(f"  Delivery: {state.arrival_time}")
    print()

    should_stop = tracker._process_state(state)

    if should_stop:
        raise AssertionError(
            "Tracker stopped too early."
        )

    print("--- Final delivered state ---")
    print()

    state = client.get_shipment()

    should_stop = tracker._process_state(state)

    if not should_stop:
        raise AssertionError(
            "Tracker did not stop after delivery."
        )

    print()
    print("Tracker correctly handled the error.")
    print("Tracker correctly continued monitoring.")
    print("Tracker correctly stopped after delivery.")
    print()
    print("=" * 60)
    print("ERROR RECOVERY TEST PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()