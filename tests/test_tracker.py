#tests/test_tracker.py

from src.models import ShipmentState
from src.tracker import Tracker


class FakeClient:
    tracking_number = "3422719707"
    postal_code = "4028"


def main() -> None:
    tracker = Tracker(
        client=FakeClient(),
        min_polling=1,
        max_polling=1,
        randomize=False,
        persist_state=False,
    )

    states = [
        ShipmentState(
            status="INDELIVERY",
            status_text="GLS járműben, kiszállítás alatt",
            arrival_time="16:00-19:00",
            last_event_time="2026-10-07",
        ),
        ShipmentState(
            status="INDELIVERY",
            status_text="GLS járműben, kiszállítás alatt",
            arrival_time="17:00-20:00",
            last_event_time="2026-10-07",
        ),
        ShipmentState(
            status="DELIVERED",
            status_text="Kézbesítve",
            arrival_time=None,
            last_event_time="2026-10-07",
        ),
    ]

    print("=" * 60)
    print("TRACKER FULL TEST")
    print("=" * 60)
    print()

    for index, state in enumerate(states, start=1):
        print(f"--- Test state {index} ---")
        print()

        should_stop = tracker._process_state(state)

        print()

        if should_stop:
            print("Tracker requested shutdown.")
            break

    print()
    print("=" * 60)
    print("TEST FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()