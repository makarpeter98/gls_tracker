#src/tracker.py

import random
import time
from datetime import datetime

from .gls_client import GLSClient
from .models import ShipmentState
from .notifier import notify
from .state_store import load_state, save_state


class Tracker:
    def __init__(
        self,
        client: GLSClient,
        min_polling: int = 60,
        max_polling: int = 120,
        randomize: bool = True,
        sound_enabled: bool = True,
        persist_state: bool = True,
    ):
        self.client = client
        self.min_polling = min_polling
        self.max_polling = max_polling
        self.randomize = randomize
        self.sound_enabled = sound_enabled
        self.persist_state = persist_state

        if self.persist_state:
            self.previous_state = load_state(
                tracking_number=self.client.tracking_number,
                postal_code=self.client.postal_code,
            )
        else:
            self.previous_state = None

        self.previous_state_loaded = self.previous_state is not None

    def run(self) -> None:
        self._print_header()

        try:
            while True:
                try:
                    state = self.client.get_shipment()

                    should_stop = self._process_state(state)

                    if should_stop:
                        print(
                            "Package delivered. "
                            "Monitoring stopped."
                        )
                        break

                except Exception as exc:
                    self._print_error(exc)

                wait_time = self._get_wait_time()

                print(
                    f"Next check in {wait_time} seconds..."
                )

                time.sleep(wait_time)

        except KeyboardInterrupt:
            print()
            print("Stopping GLS tracker...")
            print("Goodbye!")

    def _process_state(self, state: ShipmentState) -> bool:
        timestamp = datetime.now().strftime("%H:%M:%S")

        if self.previous_state is None:
            self._print_initial_state(state)

            self.previous_state = state

            if self.persist_state:
                save_state(
                    tracking_number=self.client.tracking_number,
                    postal_code=self.client.postal_code,
                    state=state,
                )

            return self._is_delivered(state)

        changes = self._detect_changes(
            self.previous_state,
            state,
        )

        if changes:
            if self.previous_state_loaded:
                message = self._build_previous_run_notification(
                    changes
                )
            else:
                message = self._build_notification(changes)

            notify(
                message,
                sound_enabled=self.sound_enabled,
            )

        else:
            print(
                f"[{timestamp}] ✓ No changes | "
                f"Status: {state.status_text} | "
                f"Delivery: {state.arrival_time}"
            )

        self.previous_state = state
        self.previous_state_loaded = False

        if self.persist_state:
            save_state(
                tracking_number=self.client.tracking_number,
                postal_code=self.client.postal_code,
                state=state,
            )

        return self._is_delivered(state)

    @staticmethod
    def _detect_changes(
        old_state: ShipmentState,
        new_state: ShipmentState,
    ) -> list[str]:
        changes = []

        if old_state.status != new_state.status:
            changes.append(
                "Status:\n"
                f"  {old_state.status_text}\n"
                f"  → {new_state.status_text}"
            )

        if old_state.arrival_time != new_state.arrival_time:
            changes.append(
                "Expected delivery:\n"
                f"  {old_state.arrival_time}\n"
                f"  → {new_state.arrival_time}"
            )

        return changes

    @staticmethod
    def _build_notification(changes: list[str]) -> str:
        return (
            "SHIPMENT UPDATED!\n\n"
            + "\n\n".join(changes)
        )

    @staticmethod
    def _build_previous_run_notification(
        changes: list[str],
    ) -> str:
        return (
            "SHIPMENT UPDATED SINCE LAST RUN!\n\n"
            + "\n\n".join(changes)
        )

    def _get_wait_time(self) -> int:
        if not self.randomize:
            return self.min_polling

        return random.randint(
            self.min_polling,
            self.max_polling,
        )

    @staticmethod
    def _is_delivered(state: ShipmentState) -> bool:
        return state.status.upper() == "DELIVERED"

    def _print_header(self) -> None:
        print("=" * 60)
        print("GLS PACKAGE TRACKER")
        print("=" * 60)
        print()
        print(
            f"Tracking number:  {self.client.tracking_number}"
        )
        print(
            f"Postal code:      {self.client.postal_code}"
        )

        if self.randomize:
            print(
                f"Polling interval: "
                f"{self.min_polling}-{self.max_polling} seconds "
                f"(random)"
            )
        else:
            print(
                f"Polling interval: "
                f"{self.min_polling} seconds"
            )

        print(
            f"Sound:            "
            f"{'enabled' if self.sound_enabled else 'disabled'}"
        )

        print()

    @staticmethod
    def _print_initial_state(state: ShipmentState) -> None:
        print("Current shipment:")
        print(
            f"  Status:            {state.status_text}"
        )
        print(
            f"  Expected delivery: {state.arrival_time}"
        )

        if state.last_event_time:
            print(
                f"  Last event:        {state.last_event_time}"
            )

        print()
        print("Monitoring started...")
        print()

    @staticmethod
    def _print_error(error: Exception) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")

        print(
            f"[{timestamp}] ERROR: {error}"
        )