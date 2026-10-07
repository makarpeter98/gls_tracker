#src/main.py

from .config import (
    get_polling_settings,
    get_postal_code,
    get_sound_enabled,
    get_tracking_number,
    load_config,
    save_config,
)
from .gls_client import GLSClient
from .tracker import Tracker


def main() -> None:
    config = load_config()

    tracking_number = get_tracking_number(config)
    postal_code = get_postal_code(config)

    if not tracking_number:
        print("Tracking number cannot be empty.")
        return

    if not postal_code:
        print("Postal code cannot be empty.")
        return

    config["tracking_number"] = tracking_number
    config["postal_code"] = postal_code

    save_config(config)

    min_polling, max_polling, randomize = get_polling_settings(
        config
    )

    sound_enabled = get_sound_enabled(config)

    client = GLSClient(
        tracking_number=tracking_number,
        postal_code=postal_code,
    )

    tracker = Tracker(
        client=client,
        min_polling=min_polling,
        max_polling=max_polling,
        randomize=randomize,
        sound_enabled=sound_enabled,
    )

    tracker.run()


if __name__ == "__main__":
    main()