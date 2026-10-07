#src/tracker.py

import random
import time
from datetime import datetime

from .gls_client import GLSClient
from .history_store import (
    append_stop_history,
    load_history,
)
from .live_tracking_client import LiveTrackingClient
from .models import LiveTrackingState, ShipmentState
from .notifier import notify
from .state_store import load_state, save_state
from .terminal_ui import TerminalUI


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
        persist_history: bool = True,
    ):
        self.client = client
        self.live_client = live_client

        self.min_polling = min_polling
        self.max_polling = max_polling
        self.randomize = randomize
        self.sound_enabled = sound_enabled

        self.persist_state = persist_state
        self.persist_history = persist_history

        self.ui = TerminalUI()

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

        if self.persist_history:
            self.history = load_history(
                tracking_number=self.client.tracking_number,
                postal_code=self.client.postal_code,
            )
        else:
            self.history = []

        self.stop_timer_started_at = None

        if self.previous_state is not None:
            self.stop_timer_started_at = (
                datetime.now().astimezone()
            )

    def run(self) -> None:
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

                self._record_stop_change(state)

                should_stop = self._process_state(
                    state
                )

                if should_stop:
                    self.ui.render(
                        tracking_number=(
                            self.client.tracking_number
                        ),
                        postal_code=(
                            self.client.postal_code
                        ),
                        status=state.status,
                        status_text=state.status_text,
                        arrival_time=(
                            state.arrival_time
                        ),
                        remaining_stops=(
                            state.remaining_stops
                        ),
                        eta=state.eta,
                        eta_min=state.eta_min,
                        eta_max=state.eta_max,
                        history=self.history,
                    )

                    print()
                    print(
                        "Package delivered. "
                        "Monitoring stopped."
                    )

                    break

                wait_time = self._get_wait_time()

                self.ui.render(
                    tracking_number=(
                        self.client.tracking_number
                    ),
                    postal_code=(
                        self.client.postal_code
                    ),
                    status=state.status,
                    status_text=state.status_text,
                    arrival_time=state.arrival_time,
                    remaining_stops=(
                        state.remaining_stops
                    ),
                    eta=state.eta,
                    eta_min=state.eta_min,
                    eta_max=state.eta_max,
                    history=self.history,
                    next_check=wait_time,
                )

                time.sleep(wait_time)

            except KeyboardInterrupt:
                self.ui.clear()

                print(
                    "Stopping GLS tracker..."
                )
                print("Goodbye!")

                break

            except Exception as exc:
                self._render_error(
                    str(exc)
                )

                wait_time = self._get_wait_time()

                time.sleep(wait_time)

    def _record_stop_change(
        self,
        state: ShipmentState,
    ) -> None:
        if not self.persist_history:
            return

        current_stops = state.remaining_stops

        if current_stops is None:
            return

        now = datetime.now().astimezone()

        if self.stop_timer_started_at is None:
            self.stop_timer_started_at = now
            return

        if self.previous_state is None:
            return

        previous_stops = (
            self.previous_state.remaining_stops
        )

        if previous_stops is None:
            self.stop_timer_started_at = now
            return

        if current_stops >= previous_stops:
            return

        elapsed_seconds = (
            now - self.stop_timer_started_at
        ).total_seconds()

        stop_delta = (
            previous_stops - current_stops
        )

        if stop_delta <= 0:
            return

        seconds_per_stop = (
            elapsed_seconds / stop_delta
        )

        for offset in range(stop_delta):
            stop_before = (
                previous_stops - offset
            )
            stop_after = stop_before - 1

            entry_timestamp = now

            self.history = append_stop_history(
                tracking_number=(
                    self.client.tracking_number
                ),
                postal_code=(
                    self.client.postal_code
                ),
                previous_stops=stop_before,
                current_stops=stop_after,
                timestamp=entry_timestamp,
                duration_seconds=(
                    seconds_per_stop
                ),
            )

        self.stop_timer_started_at = now

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
        if self.previous_state is None:
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
                f"  -> {new_state.status_text}"
            )

        if old_state.arrival_time != new_state.arrival_time:
            changes.append(
                "Expected delivery:\n"
                f"  {old_state.arrival_time}\n"
                f"  -> {new_state.arrival_time}"
            )

        if (
            old_state.remaining_stops
            != new_state.remaining_stops
        ):
            changes.append(
                "Remaining stops:\n"
                f"  {old_state.remaining_stops}\n"
                f"  -> {new_state.remaining_stops}"
            )

        if old_state.eta != new_state.eta:
            changes.append(
                "ETA:\n"
                f"  {Tracker._format_datetime(old_state.eta)}\n"
                f"  -> {Tracker._format_datetime(new_state.eta)}"
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
                f"  -> "
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
            if (
                new_state.position_lat is not None
                and new_state.position_lng is not None
            ):
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

    def _render_error(
        self,
        error: str,
    ) -> None:
        self.ui.clear()

        print(
            "+"
            + "=" * self.ui.WIDTH
            + "+"
        )

        print(
            "|"
            + " GLS PACKAGE TRACKER".ljust(
                self.ui.WIDTH
            )
            + "|"
        )

        print(
            "+"
            + "=" * self.ui.WIDTH
            + "+"
        )

        print()

        print(
            f"ERROR: {error}"
        )

        print()

        print(
            "Retrying automatically..."
        )

        print(
            "+"
            + "=" * self.ui.WIDTH
            + "+"
        )

    @staticmethod
    def _format_datetime(
        value: datetime | None,
    ) -> str:
        if value is None:
            return "N/A"

        return value.astimezone().strftime(
            "%H:%M:%S"
        )

    @staticmethod
    def _print_live_error(
        error: Exception,
    ) -> None:
        timestamp = datetime.now().strftime(
            "%H:%M:%S"
        )

        print(
            f"[{timestamp}] "
            f"LIVE API ERROR: {error}"
        )