#tests/test_live_tracking.py

from unittest.mock import Mock, patch

from src.live_tracking_client import LiveTrackingClient


def test_get_tracking() -> None:
    response_data = {
        "status": {
            "etaTimestamp": "2026-10-07T13:25:56Z",
            "etaTimestampMin": "2026-10-07T12:00:00Z",
            "etaTimestampMax": "2026-10-07T14:40:00Z",
            "remainingStops": 50,
            "position": {
                "lat": 47.535440,
                "lng": 21.643810,
            },
        }
    }

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = response_data

    client = LiveTrackingClient(
        tracking_number="1234567890",
        postal_code="1234",
    )

    with patch(
        "src.live_tracking_client.requests.get",
        return_value=response,
    ) as mock_get:
        state = client.get_tracking()

    mock_get.assert_called_once()

    assert state.remaining_stops == 50

    assert state.eta is not None
    assert state.eta_min is not None
    assert state.eta_max is not None

    assert state.position_lat == 47.535440
    assert state.position_lng == 21.643810