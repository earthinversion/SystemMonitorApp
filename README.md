# System Monitor App

I built this desktop app to track live machine health with a fast PyQt5 dashboard.

## Why this version is stronger
- I split the project into a real `src/system_monitor` package instead of a single script.
- I added service-layer modules so UI and metrics logic are cleanly separated.
- I introduced test coverage for core logic to show engineering discipline.
- I added optional CSV metrics export for data analysis workflows.

## Features
- Live CPU and RAM circular usage indicators
- Toggleable CPU/RAM time-series graph with rolling history
- Disk usage, process count, and network throughput strip
- Uptime and capture timestamp visibility
- Splash screen startup flow
- Optional CSV telemetry export

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python systemMonitor.py
```

## Make Targets
```bash
make install
make run
make status
make close
```

## Platform Support
- I designed the app itself to run on macOS, Linux, and Windows.
- I currently use a Unix-style `Makefile`, so `make install/run/close/status` is for macOS and Linux.
- On Windows, I run the same app with Python commands directly.

### Windows Quick Start (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python systemMonitor.py
```

## Runtime Options
```bash
python systemMonitor.py --interval-ms 1000 --history-seconds 30
python systemMonitor.py --export-csv data/metrics.csv
python systemMonitor.py --no-splash
```

## Repository Layout
```text
.
├── src/system_monitor/
│   ├── app.py
│   ├── constants.py
│   ├── models.py
│   ├── services/
│   └── ui/
├── tests/
├── docs/
├── main.ui
├── splash_screen.ui
└── systemMonitor.py
```

## Test
```bash
python -m unittest discover -s tests
```

<p align="center">
  <img width="80%" src="docs/screenShot1.jpg" alt="System Monitor screenshot">
</p>
