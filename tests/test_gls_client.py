#tests/test_gls_client.py

from src.gls_client import GLSClient


def main() -> None:
    client = GLSClient(
        tracking_number="3422719707",
        postal_code="4028",
    )

    shipment = client.get_shipment()

    print("Tracking number:", client.tracking_number)
    print("Status:", shipment.status)
    print("Status text:", shipment.status_text)
    print("Arrival time:", shipment.arrival_time)
    print("Last event:", shipment.last_event_time)


if __name__ == "__main__":
    main()