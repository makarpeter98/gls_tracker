#src/terminal_ui.py

import os
import sys
from datetime import datetime


class TerminalUI:
    WIDTH = 68
    BAR_WIDTH = 38
    HISTORY_BARS = 50
    MAX_STOP_TIME_SECONDS = 20 * 60

    def __init__(self):
        self._enable_ansi()

    @staticmethod
    def _enable_ansi() -> None:
        if os.name == "nt":
            os.system("")

    def clear(self) -> None:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def render(
        self,
        *,
        tracking_number: str,
        postal_code: str,
        status: str,
        status_text: str,
        arrival_time: str | None,
        remaining_stops: int | None,
        eta: datetime | None,
        eta_min: datetime | None,
        eta_max: datetime | None,
        history: list[dict],
        next_check: int | None = None,
        error: str | None = None,
    ) -> None:
        self.clear()

        print(
            "+"
            + "=" * self.WIDTH
            + "+"
        )

        print(
            "|"
            + self._center(
                "GLS PACKAGE TRACKER",
                self.WIDTH,
            )
            + "|"
        )

        print(
            "+"
            + "=" * self.WIDTH
            + "+"
        )

        self._line(
            "Tracking",
            tracking_number,
        )

        self._line(
            "Postal code",
            postal_code,
        )

        self._separator()

        self._line(
            "Status",
            status_text or status or "N/A",
        )

        self._line(
            "Delivery",
            arrival_time or "N/A",
        )

        self._line(
            "Remaining stops",
            (
                str(remaining_stops)
                if remaining_stops is not None
                else "N/A"
            ),
        )

        self._line(
            "ETA",
            self._format_datetime(eta),
        )

        self._line(
            "ETA window",
            (
                f"{self._format_time(eta_min)}"
                f" - "
                f"{self._format_time(eta_max)}"
            ),
        )

        self._separator()

        self._render_stop_time_chart(
            history
        )

        self._separator()

        now = datetime.now().strftime(
            "%H:%M:%S"
        )

        self._line(
            "Last update",
            now,
        )

        if next_check is not None:
            self._line(
                "Next check",
                f"{next_check}s",
            )

        if error:
            self._separator()

            self._line(
                "ERROR",
                error,
            )

        print(
            "+"
            + "=" * self.WIDTH
            + "+"
        )

        print(
            "  Ctrl+C = stop"
        )

        sys.stdout.flush()

    def _render_stop_time_chart(
        self,
        history: list[dict],
    ) -> None:
        print(
            "|  STOP DELIVERY TIME"
        )

        entries = []

        for entry in history:
            stop = entry.get("stop")
            duration = entry.get(
                "duration_seconds"
            )

            if not isinstance(
                stop,
                int,
            ):
                continue

            if not isinstance(
                duration,
                (int, float),
            ):
                continue

            entries.append(
                {
                    "stop": stop,
                    "duration": float(duration),
                }
            )

        if not entries:
            print(
                "|  Waiting for stop changes..."
            )
            return

        entries = entries[
            -self.HISTORY_BARS:
        ]

        for entry in reversed(entries):
            stop = entry["stop"]
            duration = entry["duration"]

            bar = self._build_stop_bar(
                duration
            )

            duration_text = (
                self._format_duration(
                    duration
                )
            )

            print(
                "|  "
                f"{stop:>2}: "
                f"{bar} "
                f"{duration_text:>7}"
            )

    def _build_stop_bar(
        self,
        duration_seconds: float,
    ) -> str:
        ratio = min(
            duration_seconds
            / self.MAX_STOP_TIME_SECONDS,
            1.0,
        )

        filled = int(
            ratio * self.BAR_WIDTH
        )

        if duration_seconds > 0:
            filled = max(
                filled,
                1,
            )

        empty = (
            self.BAR_WIDTH
            - filled
        )

        return (
            self._bar_color(
                "█" * filled,
                duration_seconds,
            )
            + "░" * empty
        )

    @staticmethod
    def _bar_color(
        bar: str,
        duration_seconds: float,
    ) -> str:
        if duration_seconds <= 5 * 60:
            color = "\033[92m"
        elif duration_seconds <= 10 * 60:
            color = "\033[93m"
        elif duration_seconds <= 15 * 60:
            color = "\033[33m"
        else:
            color = "\033[91m"

        reset = "\033[0m"

        return (
            f"{color}"
            f"{bar}"
            f"{reset}"
        )

    def _line(
        self,
        label: str,
        value: str,
    ) -> None:
        content = (
            f"  "
            f"{label:<18} "
            f"{value}"
        )

        print(
            "|"
            + content[:self.WIDTH].ljust(
                self.WIDTH
            )
            + "|"
        )

    def _separator(self) -> None:
        print(
            "+"
            + "-" * self.WIDTH
            + "+"
        )

    @staticmethod
    def _center(
        value: str,
        width: int,
    ) -> str:
        return value.center(
            width
        )

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
    def _format_time(
        value: datetime | None,
    ) -> str:
        if value is None:
            return "N/A"

        return value.astimezone().strftime(
            "%H:%M:%S"
        )

    @staticmethod
    def _format_duration(
        seconds: float,
    ) -> str:
        seconds = max(
            0,
            int(seconds),
        )

        minutes, remaining_seconds = divmod(
            seconds,
            60,
        )

        if minutes > 0:
            return (
                f"{minutes}m "
                f"{remaining_seconds:02d}s"
            )

        return f"{remaining_seconds}s"