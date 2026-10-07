#src/live_tracking_client.py

from datetime import datetime

import requests

from .models import LiveTrackingState


class LiveTrackingClient:
    BASE_URL = (
        "https://api.gls-rtt.com/v1/tenant/gls-hu/"
        "parcel/{tracking_number}/{postal_code}"
    )

    HEADERS = {
        "Origin": "https://gls-rtt.com",
        "Referer": "https://gls-rtt.com/",
        "x-original-hostname": "gls-rtt.com",
        "x-original-referrer-hostname": "gls-rtt.com",
        "x-original-utm-source": "invite-email",
    }

    def __init__(
        self,
        tracking_number: str,
        postal_code: str,
    ):
        self.tracking_number = tracking_number
        self.postal_code = postal_code

    def get_tracking(self) -> LiveTrackingState:
        url = self.BASE_URL.format(
            tracking_number=self.tracking_number,
            postal_code=self.postal_code,
        )

        try:
            response = requests.get(
                url,
                headers=self.HEADERS,
                timeout=15,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"GLS live tracking request failed: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "GLS live tracking returned invalid JSON."
            ) from exc

        try:
            return self._parse_response(data)

        except (TypeError, ValueError, AttributeError) as exc:
            raise RuntimeError(
                "GLS live tracking response has an unexpected format."
            ) from exc

    @staticmethod
    def _parse_response(
        data: dict,
    ) -> LiveTrackingState:
        status = data.get("status", {})

        if not isinstance(status, dict):
            raise TypeError(
                "GLS live tracking status is not an object."
            )

        position = status.get("position")

        position_lat = None
        position_lng = None

        if isinstance(position, dict):
            position_lat = LiveTrackingClient._parse_float(
                position.get("lat")
            )
            position_lng = LiveTrackingClient._parse_float(
                position.get("lng")
            )

        return LiveTrackingState(
            eta=LiveTrackingClient._parse_datetime(
                status.get("etaTimestamp")
            ),
            eta_min=LiveTrackingClient._parse_datetime(
                status.get("etaTimestampMin")
            ),
            eta_max=LiveTrackingClient._parse_datetime(
                status.get("etaTimestampMax")
            ),
            remaining_stops=LiveTrackingClient._parse_int(
                status.get("remainingStops")
            ),
            position_lat=position_lat,
            position_lng=position_lng,
        )

    @staticmethod
    def _parse_datetime(
        value,
    ) -> datetime | None:
        if not value:
            return None

        if not isinstance(value, str):
            return None

        try:
            return datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )

        except ValueError:
            return None

    @staticmethod
    def _parse_int(
        value,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(value)

        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_float(
        value,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)

        except (TypeError, ValueError):
            return None