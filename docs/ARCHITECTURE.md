# Architecture

I organized the app into three small layers so I can ship features without touching unrelated code.

## UI Layer
- `src/system_monitor/ui/main_window.py`
- `src/system_monitor/ui/splash_screen.py`

I keep Qt rendering and widget behavior here.

## Service Layer
- `src/system_monitor/services/system_stats.py`
- `src/system_monitor/services/history_buffer.py`
- `src/system_monitor/services/csv_exporter.py`

I isolate data collection, history buffering, and export concerns here.

## Core Models
- `src/system_monitor/models.py`

I use a typed `SystemSnapshot` object as the contract between the services and UI.

## App Entry
- `src/system_monitor/app.py`
- `systemMonitor.py`

I parse runtime flags in `app.py` and keep `systemMonitor.py` as a compatibility launcher.
