#src/config.py

import json
from pathlib import Path


CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "tracking_number": "",
    "postal_code": "",
    "min_polling": 60,
    "max_polling": 120,
    "randomize": True,
    "sound_enabled": True,
}

DEFAULT_MIN_POLLING = 60
DEFAULT_MAX_POLLING = 120
DEFAULT_RANDOMIZE = True
DEFAULT_SOUND_ENABLED = True


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        print("config.json was not found.")
        print("Creating configuration...")
        print()

        config = create_config()

        print()
        print("Configuration saved.")
        print()

        return config

    try:
        with CONFIG_FILE.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError:
        print(
            "Warning: config.json contains invalid JSON."
        )
        return DEFAULT_CONFIG.copy()


def create_config() -> dict:
    config = DEFAULT_CONFIG.copy()

    config["tracking_number"] = input(
        "Tracking number: "
    ).strip()

    config["postal_code"] = input(
        "Postal code: "
    ).strip()

    save_config(config)

    return config


def save_config(config: dict) -> None:
    with CONFIG_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            config,
            file,
            ensure_ascii=False,
            indent=4,
        )


def get_tracking_number(config: dict) -> str:
    tracking_number = config.get("tracking_number")

    if isinstance(tracking_number, str):
        tracking_number = tracking_number.strip()

        if tracking_number:
            return tracking_number

    return input("Tracking number: ").strip()


def get_postal_code(config: dict) -> str:
    postal_code = config.get("postal_code")

    if isinstance(postal_code, str):
        postal_code = postal_code.strip()

        if postal_code:
            return postal_code

    return input("Postal code: ").strip()


def get_polling_settings(
    config: dict,
) -> tuple[int, int, bool]:
    min_polling = _get_positive_int(
        config.get("min_polling"),
        DEFAULT_MIN_POLLING,
    )

    max_polling = _get_positive_int(
        config.get("max_polling"),
        DEFAULT_MAX_POLLING,
    )

    if max_polling < min_polling:
        max_polling = min_polling

    randomize = config.get(
        "randomize",
        DEFAULT_RANDOMIZE,
    )

    if not isinstance(randomize, bool):
        randomize = DEFAULT_RANDOMIZE

    return min_polling, max_polling, randomize


def get_sound_enabled(config: dict) -> bool:
    sound_enabled = config.get(
        "sound_enabled",
        DEFAULT_SOUND_ENABLED,
    )

    if not isinstance(sound_enabled, bool):
        return DEFAULT_SOUND_ENABLED

    return sound_enabled


def _get_positive_int(
    value,
    default: int,
) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    if value < 1:
        return default

    return value