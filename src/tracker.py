#src/tracker.py

import random
import time
from datetime import datetime

from .gls_client import GLSClient
from .live_tracking_client import LiveTrackingClient
from .models import LiveTrackingState, ShipmentState
from .notifier import notify
from .state_store import load_state, save_state


class Tracker:
    def __init__(
        self,
        client: GLSClient,
        live_client: LiveTrackingClient | None = None,
        min_polling: int = 60,
        max_polling: int = 120,
        randomize: bool = True,
        sound_enabled: bool = True,
        persist_state: bool = True,
    ):
        self.client = client
        self.live_client = live_client

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

        self.previous_state_loaded = (
            self.previous_state is not None
        )

    def run(self) -> None:
        self._print_header()

        try:
            while True:
                try:
                    shipment = self.client.get_shipment()

                    live = None

                    if self.live_client is not None:
                        try:
                            live = (
                                self.live_client.get_tracking()
                            )

                        except Exception as exc:
                            self._print_live_error(exc)

                    state = self._merge_states(
                        shipment,
                        live,
                    )

                    should_stop = self._process_state(
                        state
                    )

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

    @staticmethod
    def _merge_states(
        shipment: ShipmentState,
        live: LiveTrackingState | None,
    ) -> ShipmentState:
        if live is None:
            return shipment

        return ShipmentState(
            status=shipment.status,
            status_text=shipment.status_text,
            arrival_time=shipment.arrival_time,
            last_event_time=shipment.last_event_time,
            eta=live.eta,
            eta_min=live.eta_min,
            eta_max=live.eta_max,
            remaining_stops=live.remaining_stops,
            position_lat=live.position_lat,
            position_lng=live.position_lng,
        )

    def _process_state(
        self,
        state: ShipmentState,
    ) -> bool:
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        if self.previous_state is None:
            self._print_initial_state(state)

            self.previous_state = state

            if self.persist_state:
                save_state(
                    tracking_number=(
                        self.client.tracking_number
                    ),
                    postal_code=(
                        self.client.postal_code
                    ),
                    state=state,
                )

            return self._is_delivered(state)

        changes = self._detect_changes(
            self.previous_state,
            state,
        )

        if changes:
            if self.previous_state_loaded:
                message = (
                    self._build_previous_run_notification(
                        changes
                    )
                )
            else:
                message = self._build_notification(
                    changes
                )

            notify(
                message,
                sound_enabled=self.sound_enabled,
            )

        else:
            print(
                f"[{timestamp}] ✓ No changes | "
                f"Status: {state.status_text} | "
                f"Delivery: {state.arrival_time} | "
                f"Stops: {state.remaining_stops} | "
                f"ETA: {self._format_datetime(state.eta)}"
            )

        self.previous_state = state
        self.previous_state_loaded = False

        if self.persist_state:
            save_state(
                tracking_number=(
                    self.client.tracking_number
                ),
                postal_code=(
                    self.client.postal_code
                ),
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

        if (
            old_state.remaining_stops
            != new_state.remaining_stops
        ):
            changes.append(
                "Remaining stops:\n"
                f"  {old_state.remaining_stops}\n"
                f"  → {new_state.remaining_stops}"
            )

        if old_state.eta != new_state.eta:
            changes.append(
                "ETA:\n"
                f"  {Tracker._format_datetime(old_state.eta)}\n"
                f"  → {Tracker._format_datetime(new_state.eta)}"
            )

        if (
            old_state.eta_min != new_state.eta_min
            or old_state.eta_max != new_state.eta_max
        ):
            changes.append(
                "ETA window:\n"
                f"  "
                f"{Tracker._format_datetime(old_state.eta_min)}"
                f" - "
                f"{Tracker._format_datetime(old_state.eta_max)}\n"
                f"  → "
                f"{Tracker._format_datetime(new_state.eta_min)}"
                f" - "
                f"{Tracker._format_datetime(new_state.eta_max)}"
            )

        if (
            old_state.position_lat
            != new_state.position_lat
            or old_state.position_lng
            != new_state.position_lng
        ):
            if new_state.has_position:
                changes.append(
                    "Courier position:\n"
                    f"  {new_state.position_lat:.6f}, "
                    f"{new_state.position_lng:.6f}"
                )

        return changes

    @staticmethod
    def _build_notification(
        changes: list[str],
    ) -> str:
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
    def _is_delivered(
        state: ShipmentState,
    ) -> bool:
        return state.status.upper() in {
            "DELIVERED",
            "DELIVERY",
        }

    def _print_header(self) -> None:
        print("=" * 60)
        print("GLS PACKAGE TRACKER")
        print("=" * 60)
        print()
        print(
            f"Tracking number:  "
            f"{self.client.tracking_number}"
        )
        print(
            f"Postal code:      "
            f"{self.client.postal_code}"
        )

        if self.randomize:
            print(
                f"Polling interval: "
                f"{self.min_polling}-"
                f"{self.max_polling} seconds "
                f"(random)"
            )
        else:
            print(
                f"Polling interval: "
                f"{self.min_polling} seconds"
            )

        print(
            "Sound:            "
            f"{'enabled' if self.sound_enabled else 'disabled'}"
        )

        print()

    @staticmethod
    def _print_initial_state(
        state: ShipmentState,
    ) -> None:
        print("Current shipment:")
        print(
            f"  Status:            "
            f"{state.status_text}"
        )
        print(
            f"  Expected delivery: "
            f"{state.arrival_time}"
        )
        print(
            f"  ETA:               "
            f"{Tracker._format_datetime(state.eta)}"
        )
        print(
            f"  ETA window:        "
            f"{Tracker._format_datetime(state.eta_min)}"
            f" - "
            f"{Tracker._format_datetime(state.eta_max)}"
        )
        print(
            f"  Remaining stops:   "
            f"{state.remaining_stops}"
        )

        if (
            state.position_lat is not None
            and state.position_lng is not None
        ):
            print(
                f"  Courier position:  "
                f"{state.position_lat:.6f}, "
                f"{state.position_lng:.6f}"
            )
        else:
            print(
                "  Courier position:  "
                "not available"
            )

        if state.last_event_time:
            print(
                f"  Last event:        "
                f"{state.last_event_time}"
            )

        print()
        print("Monitoring started...")
        print()

    @staticmethod
    def _format_datetime(
        value: datetime | None,
    ) -> str:
        if value is None:
            return "N/A"

        return value.astimezone().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    @staticmethod
    def _print_error(
        error: Exception,
    ) -> None:
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        print(
            f"[{timestamp}] ERROR: {error}"
        )

    @staticmethod
    def _print_live_error(
        error: Exception,
    ) -> None:
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        print(
            f"[{timestamp}] LIVE API ERROR: {error}"
        )