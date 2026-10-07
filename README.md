# GLS Package Tracker

A lightweight Python application for monitoring GLS parcel deliveries.

The application periodically checks the GLS tracking API and detects changes in:

* shipment status
* expected delivery time

When a change is detected, the tracker displays a notification in the console and can optionally play a sound.

The tracker automatically stops when the shipment is marked as delivered.

## Features

* GLS tracking API integration
* Configurable tracking number and postal code
* Configurable polling interval
* Optional randomized polling interval
* Shipment status change detection
* Expected delivery time change detection
* Persistent state between application runs
* Console notifications
* Optional Windows notification sound
* Automatic shutdown after delivery
* Error handling for API/network failures
* No external database required

## Requirements

* Windows
* Python 3.11 or newer
* Internet connection
* A valid GLS tracking number
* GLS postal code associated with the shipment

The application uses Windows `winsound` for notification sounds, so the current version is Windows-specific.

## Installation

Clone the repository and enter the project directory:

powershell
git clone <repository-url>
cd gls_tracker


Create a virtual environment:

powershell
python -m venv gls_tracker_venv


Activate it:

powershell
.\gls_tracker_venv\Scripts\Activate.ps1


Install the required dependency:

powershell
pip install -r requirements.txt


## Configuration

On the first start, the application creates `config.json` and asks for the tracking number and postal code.

The configuration looks like this:

json
{
    "tracking_number": "",
    "postal_code": "",
    "min_polling": 60,
    "max_polling": 120,
    "randomize": true,
    "sound_enabled": true
}


### Configuration options

| Option            | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `tracking_number` | GLS shipment tracking number                                   |
| `postal_code`     | Postal code associated with the shipment                       |
| `min_polling`     | Minimum polling interval in seconds                            |
| `max_polling`     | Maximum polling interval in seconds                            |
| `randomize`       | Randomize the polling interval between the minimum and maximum |
| `sound_enabled`   | Enable or disable notification sounds                          |

The included `config.example.json` can also be used as a template.

## Running

After activating the virtual environment:

powershell
python -m src.main


Alternatively, use the included `start.txt` as a quick reference:

text
.\gls_tracker_venv\Scripts\Activate.ps1
python -m src.main


## Example

A normal run looks similar to:

text
============================================================
GLS PACKAGE TRACKER
============================================================

Tracking number:  1234567890
Postal code:      1234
Polling interval: 60-120 seconds (random)
Sound:            enabled

[11:37:11] ✓ No changes | Status: GLS járműben, kiszállítás alatt | Delivery: 16:00-19:00
Next check in 60 seconds...


When the expected delivery time changes:

text
============================================================
[11:42:46] 🔔 SHIPMENT UPDATED!

Expected delivery:
  16:00-19:00
  → 17:00-20:00
============================================================


When the shipment is delivered:

text
============================================================
[11:42:47] 🔔 SHIPMENT UPDATED!

Status:
  GLS járműben, kiszállítás alatt
  → Kézbesítve

Expected delivery:
  17:00-20:00
  → None
============================================================

Package delivered. Monitoring stopped.


## Persistent State

The tracker stores the last known shipment state in:

text
data/last_state.json


This allows the application to detect changes that happened while the tracker was not running.

For example, if the expected delivery time changes while the application is closed, the next startup can report:

text
SHIPMENT UPDATED SINCE LAST RUN!
Runtime state is excluded from Git through `.gitignore`.

## Project Structure

text
gls_tracker/
├── sounds/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── gls_client.py
│   ├── main.py
│   ├── models.py
│   ├── notifier.py
│   ├── state_store.py
│   └── tracker.py
├── tests/
│   ├── __init__.py
│   ├── test_gls_client.py
│   ├── test_gls_errors.py
│   ├── test_tracker.py
│   └── test_tracker_errors.py
├── .gitignore
├── config.example.json
├── README.md
├── requirements.txt
└── start.txt


### Source modules

#### `gls_client.py`

Handles communication with the GLS tracking API and converts the API response into a `ShipmentState` object.

#### `models.py`

Contains the data model used to represent the current shipment state.

#### `tracker.py`

Contains the main monitoring logic:

* state comparison
* change detection
* polling
* persistent state handling
* delivery detection
* error recovery

#### `config.py`

Loads, creates and validates the application configuration.

#### `state_store.py`

Stores and loads the last known shipment state.

#### `notifier.py`

Displays console notifications and optionally plays a Windows sound.

#### `main.py`

Application entry point. It connects configuration, the GLS client and the tracker.

## Testing

The project includes tests for the GLS client and tracker.

Run the GLS API client test:

powershell
python -m tests.test_gls_client


Run the tracker test:

powershell
python -m tests.test_tracker


Run the GLS error handling tests:

powershell
python -m tests.test_gls_errors


Run the tracker error recovery test:

powershell
python -m tests.test_tracker_errors


The tests cover:

* successful GLS API requests
* network/API errors
* invalid JSON responses
* unexpected API response formats
* shipment state changes
* delivery detection
* tracker recovery after errors
* persistent-state-independent tracker operation

## Polling

The default polling interval is 60–120 seconds with randomization enabled.

Randomized polling helps avoid sending requests at exactly the same interval every time.

For development and testing, shorter intervals can be configured, for example:

json
{
    "min_polling": 10,
    "max_polling": 15,
    "randomize": true
}


For normal operation, a longer interval is recommended.

## Current Limitations

The tracker currently monitors the information exposed by the GLS tracking API.

It does **not** provide:

* driver's live GPS position
* number of stops remaining
* current position in the delivery queue
* total number of deliveries before the shipment
* exact arrival prediction beyond the delivery window provided by GLS

These values are not currently exposed by the GLS tracking endpoint used by the application.

## Security and Privacy

`config.json` is intentionally excluded from Git.

This prevents personal tracking numbers and postal codes from being committed to the repository.

The example configuration contains no real shipment information.

## License

No license has been selected yet.
