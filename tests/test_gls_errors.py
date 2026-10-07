#tests/test_gls_errors.py

from unittest.mock import patch

import requests

from src.gls_client import GLSClient


def test_request_error() -> None:
    client = GLSClient(
        tracking_number="3422719707",
        postal_code="4028",
    )

    with patch(
        "src.gls_client.requests.get"
    ) as mock_get:
        mock_get.side_effect = requests.ConnectionError(
            "Test connection error"
        )

        try:
            client.get_shipment()

        except RuntimeError as exc:
            print("Request error test:")
            print(f"  {exc}")
            print("  PASS")
            return

    raise AssertionError(
        "Expected RuntimeError was not raised."
    )


def test_invalid_json() -> None:
    client = GLSClient(
        tracking_number="3422719707",
        postal_code="4028",
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            raise ValueError("Invalid JSON")

    with patch(
        "src.gls_client.requests.get",
        return_value=FakeResponse(),
    ):
        try:
            client.get_shipment()

        except RuntimeError as exc:
            print("Invalid JSON test:")
            print(f"  {exc}")
            print("  PASS")
            return

    raise AssertionError(
        "Expected RuntimeError was not raised."
    )


def test_unexpected_format() -> None:
    client = GLSClient(
        tracking_number="3422719707",
        postal_code="4028",
    )

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "progressBar": None,
            }

    with patch(
        "src.gls_client.requests.get",
        return_value=FakeResponse(),
    ):
        try:
            client.get_shipment()

        except RuntimeError as exc:
            print("Unexpected format test:")
            print(f"  {exc}")
            print("  PASS")
            return

    raise AssertionError(
        "Expected RuntimeError was not raised."
    )


def main() -> None:
    print("=" * 60)
    print("GLS CLIENT ERROR TEST")
    print("=" * 60)
    print()

    test_request_error()
    print()

    test_invalid_json()
    print()

    test_unexpected_format()
    print()

    print("=" * 60)
    print("ALL ERROR TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()