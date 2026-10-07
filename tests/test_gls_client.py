#tests/test_gls_client.py

from unittest.mock import Mock, patch

from src.gls_client import GLSClient


def test_get_shipment() -> None:
    response_data = {
        "arrivalTime": {
            "value": "16:00-19:00",
        },
        "progressBar": {
            "statusInfo": "INDELIVERY",
            "statusText": "GLS vehicle, out for delivery",
        },
        "history": [
            {
                "date": "2026-10-07",
            }
        ],
    }

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = response_data

    client = GLSClient(
        tracking_number="1234567890",
        postal_code="1234",
    )

    with patch(
        "src.gls_client.requests.get",
        return_value=response,
    ) as mock_get:
        shipment = client.get_shipment()

    mock_get.assert_called_once()

    assert shipment.status == "INDELIVERY"
    assert shipment.status_text == (
        "GLS vehicle, out for delivery"
    )
    assert shipment.arrival_time == "16:00-19:00"
    assert shipment.last_event_time == "2026-10-07"