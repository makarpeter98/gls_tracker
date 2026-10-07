# GLS Package Tracker

A lightweight Python application for monitoring GLS parcel deliveries in real time.

The tracker periodically checks the GLS tracking API and the GLS live tracking API, combines the returned information into a single shipment state, detects changes, and displays the current status in a live terminal dashboard.

The application also records delivery-stop telemetry, allowing the terminal interface to show how long individual delivery stops take over time.

Optional Windows sound notifications can be enabled.

The application automatically stops monitoring when the shipment is delivered.

## Features

* GLS shipment tracking API integration
* GLS live tracking integration
* Shipment status monitoring
* Expected delivery window monitoring
* Live ETA monitoring
* Live ETA window monitoring
* Remaining delivery stops
* Courier position when provided by GLS
* Detection of multiple changes in a single polling cycle
* Persistent shipment state between application runs
* Detection of changes that happened while the application was not running
* Persistent delivery-stop telemetry history
* Stop delivery time visualization
* Terminal dashboard with live status information
* Console notifications
* Optional Windows notification sound
* Configurable polling interval
* Optional randomized polling interval
* Automatic shutdown after delivery
* Error handling for API and network failures
* No external database required

## Requirements

* Windows
* Python 3.11 or newer
* Internet connection
* A valid GLS tracking number
* The postal code associated with the shipment

The current version uses Windows `winsound` for notification sounds and is therefore Windows-specific.

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


Install the application dependencies:

powershell
python -m pip install -r requirements.txt


For development and testing, install pytest if it is not already available:

powershell
python -m pip install pytest


## Configuration

On the first start, the application creates `config.json` and asks for the tracking number and postal code.

The configuration file looks like this:

json
{
    "tracking_number": "",
    "postal_code": "",
    "min_polling": 60,
    "max_polling": 120,
    "randomize": true,
    "sound_enabled": true
}


The included `config.example.json` can also be used as a template.

### Configuration options

| Option            | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| `tracking_number` | GLS shipment tracking number                                   |
| `postal_code`     | Postal code associated with the shipment                       |
| `min_polling`     | Minimum polling interval in seconds                            |
| `max_polling`     | Maximum polling interval in seconds                            |
| `randomize`       | Randomize the polling interval between the minimum and maximum |
| `sound_enabled`   | Enable or disable notification sounds                          |

For normal operation, a polling interval of approximately 60–120 seconds is recommended.

## Running

After activating the virtual environment:

powershell
python -m src.main


Alternatively, use the included `start.txt` as a quick reference:

powershell
.\gls_tracker_venv\Scripts\Activate.ps1
python -m src.main


## Terminal Dashboard

The tracker provides a live terminal dashboard containing:

* tracking number
* postal code
* shipment status
* expected delivery window
* remaining delivery stops
* current ETA
* ETA window
* stop delivery-time history
* last update time
* next scheduled API check

Example:

text
+====================================================================+
|                        GLS PACKAGE TRACKER                         |
+====================================================================+
|  Tracking           **********                                     |
|  Postal code        ****                                           |
+--------------------------------------------------------------------+
|  Status             GLS jarmuben, kiszallitas alatt                |
|  Delivery           16:00-19:00                                    |
|  Remaining stops    16                                             |
|  ETA                2026-10-07 16:28:25                            |
|  ETA window         15:40:00 - 17:40:00                            |
+--------------------------------------------------------------------+
|  STOP DELIVERY TIME
|  27: ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  3m 59s
|  26: ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  3m 52s
|  25: ███████░░░░░░░░░░░░░░░░░░░░░░░░░░░  3m 52s
|  24: █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2m 58s
|  23: █████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  2m 58s
+--------------------------------------------------------------------+
|  Last update        15:15:55
|  Next check         39s
+====================================================================+
  Ctrl+C = stop


The stop-time chart uses a 0–20 minute scale.

The history is based on actual changes in `remaining_stops`. Normal polling cycles do not create additional history entries.

## Stop Delivery Telemetry

The tracker records a history entry when the number of remaining stops decreases.

For example:

text
23 → 21


represents two completed delivery stops.

The elapsed time between known stop changes is divided across the completed stops. This allows the application to estimate the average delivery time per stop even when GLS reports multiple stops being completed between two polling cycles.

The telemetry is stored in:

text
data/history.json


Example structure:

json
{
    "tracking_number": "",
    "postal_code": "",
    "history": [
        {
            "previous_stops": 23,
            "stop": 22,
            "timestamp": "2026-10-07T14:50:46+02:00",
            "duration_seconds": 350.0
        },
        {
            "previous_stops": 23,
            "stop": 21,
            "timestamp": "2026-10-07T14:50:46+02:00",
            "duration_seconds": 350.0
        }
    ]
}


The telemetry is local runtime data and is excluded from Git through `.gitignore`.

## Historical Data Generation

For development and visualization testing, the project includes:

text
tests/history_generator.py


This can generate a `data/history.json` file from previously recorded shipment events.

Run it with:

powershell
python -m tests.history_generator


The generated file is intended for local testing and is not committed to the repository.

## Monitoring

The tracker combines information from two GLS endpoints into a single shipment state.

### Standard tracking information

The standard tracking API provides information such as:

* shipment status
* status text
* expected delivery window
* latest shipment event

### Live tracking information

When available, the live tracking API provides:

* estimated arrival time
* minimum ETA
* maximum ETA
* remaining delivery stops
* courier position

Some live tracking information may not always be available.

For example, the courier position can be unavailable even while the shipment is out for delivery.

The tracker continues monitoring the shipment if the live tracking endpoint temporarily fails.

## Change Detection

The tracker compares the current shipment state with the previously known state.

A notification is generated when one or more of the following changes:

* shipment status
* expected delivery window
* remaining stops
* ETA
* ETA window
* courier position availability or value

If several values change during the same polling cycle, they are combined into a single notification.

Example:

text
============================================================
[14:39:06] SHIPMENT UPDATED!

Remaining stops:
  25
  → 23

ETA:
  2026-10-07 16:10:37
  → 2026-10-07 16:12:45

ETA window:
  2026-10-07 15:15:00 - 2026-10-07 17:25:00
  →
  2026-10-07 15:20:00 - 2026-10-07 17:25:00
============================================================


## Persistent State

The tracker stores the last known shipment state in:

text
data/last_state.json


This allows the application to detect changes that happened while the tracker was not running.

For example, if the delivery window or ETA changes while the application is closed, the next startup can report:

text
============================================================
SHIPMENT UPDATED SINCE LAST RUN!
============================================================


Runtime state is excluded from Git through `.gitignore`.

## Delivery Detection

When the shipment reaches a delivered state, the tracker reports the final update and stops monitoring:

text
Package delivered. Monitoring stopped.


This prevents unnecessary API requests after delivery.

## Polling

The default polling interval is 60–120 seconds with randomization enabled.

Example:

json
{
    "min_polling": 60,
    "max_polling": 120,
    "randomize": true
}


With randomization enabled, each polling interval is selected randomly between the configured minimum and maximum values.

For development and testing, shorter intervals can be used:

json
{
    "min_polling": 10,
    "max_polling": 15,
    "randomize": true
}


Short polling intervals are intended for development/testing rather than normal operation.

## Testing

The project uses `pytest`.

Run all tests with:

powershell
python -m pytest


The test suite does not require a real GLS shipment or a live internet connection. External API responses are mocked where appropriate.

Current tests cover:

* successful GLS API response parsing
* GLS API request errors
* invalid JSON responses
* unexpected API response formats
* live tracking response parsing
* ETA parsing
* remaining stop parsing
* courier position parsing
* shipment state changes
* delivery detection
* tracker recovery after API errors

Example:

text
7 passed


## Project Structure

text
gls_tracker/
├── sounds/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── gls_client.py
│   ├── history_store.py
│   ├── live_tracking_client.py
│   ├── main.py
│   ├── models.py
│   ├── notifier.py
│   ├── state_store.py
│   ├── terminal_ui.py
│   └── tracker.py
├── tests/
│   ├── __init__.py
│   ├── history_generator.py
│   ├── test_gls_client.py
│   ├── test_gls_errors.py
│   ├── test_live_tracking.py
│   ├── test_tracker.py
│   └── test_tracker_errors.py
├── .gitignore
├── config.example.json
├── README.md
├── requirements.txt
└── start.txt


## Runtime Data

The following files are generated locally and are intentionally excluded from Git:

text
config.json
data/last_state.json
data/history.json


This keeps shipment-specific information and telemetry out of the public repository.

## Disclaimer

This project is an independent personal project and is not affiliated with or endorsed by GLS.

The application relies on publicly accessible GLS web/API functionality and may stop working if GLS changes its endpoints, request requirements, response formats, or access policies.
