#src/gls_client.py

import time

import requests

from .models import ShipmentState


class GLSClient:
    BASE_URL = (
        "https://gls-group.eu/app/service/open/rest/HU/hu/"
        "rstt028/{tracking_number}"
    )

    def __init__(
        self,
        tracking_number: str,
        postal_code: str,
    ):
        self.tracking_number = tracking_number
        self.postal_code = postal_code

    def get_shipment(self) -> ShipmentState:
        url = self.BASE_URL.format(
            tracking_number=self.tracking_number
        )

        params = {
            "caller": "witt002",
            "millis": int(time.time() * 1000),
            "tuOwnerCode": "HU01",
            "postalCode": self.postal_code,
        }

        try:
            response = requests.get(
                url,
                params=params,
                timeout=15,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"GLS API request failed: {exc}"
            ) from exc

        try:
            data = response.json()

        except ValueError as exc:
            raise RuntimeError(
                "GLS API returned invalid JSON."
            ) from exc

        try:
            return self._parse_response(data)

        except (
            KeyError,
            IndexError,
            TypeError,
            AttributeError,
        ) as exc:
            raise RuntimeError(
                "GLS API response has an unexpected format."
            ) from exc

    @staticmethod
    def _parse_response(
        data: dict,
    ) -> ShipmentState:
        arrival_time = data.get(
            "arrivalTime",
            {},
        )

        progress_bar = data.get(
            "progressBar",
            {},
        )

        history = data.get(
            "history",
            [],
        )

        return ShipmentState(
            status=progress_bar.get(
                "statusInfo",
                "",
            ),
            status_text=progress_bar.get(
                "statusText",
                "",
            ),
            arrival_time=arrival_time.get(
                "value",
            ),
            last_event_time=(
                history[0].get("date")
                if history
                else None
            ),
        )
  