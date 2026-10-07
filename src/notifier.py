#src/notifier.py

import winsound
from datetime import datetime


def notify(
    message: str,
    sound_enabled: bool = True,
) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")

    print()
    print("=" * 60)
    print(f"[{timestamp}] 🔔 {message}")
    print("=" * 60)
    print()

    if sound_enabled:
        winsound.Beep(1000, 300)
        winsound.Beep(1400, 300)