SHELL := /bin/bash
PYTHON ?= python3
VENV ?= .venv
VENV_PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PID_FILE := .system-monitor.pid
LOG_FILE := .system-monitor.log
APP_ARGS ?=

.PHONY: help install run close status

help:
	@echo "Targets:"
	@echo "  make install  - create virtualenv and install dependencies"
	@echo "  make run      - start the app in background and save PID"
	@echo "  make close    - stop the running app instance"
	@echo "  make status   - show whether app is running"

install:
	@test -d $(VENV) || $(PYTHON) -m venv $(VENV)
	@$(PIP) install --upgrade pip
	@$(PIP) install -r requirements.txt

run:
	@test -x $(VENV_PY) || (echo "Virtual environment missing. Run 'make install' first." && exit 1)
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "App is already running with PID $$(cat $(PID_FILE))."; \
		exit 0; \
	fi
	@QT_PLUGIN_SRC="$$( $(VENV_PY) -c 'import PyQt5; from pathlib import Path; print((Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins").as_posix())' )"; \
	QT_PLATFORM_SRC="$$QT_PLUGIN_SRC/platforms"; \
	QT_PLUGIN_PATH_RUN="$$QT_PLUGIN_SRC"; \
	QT_QPA_PLATFORM_PLUGIN_PATH_RUN="$$QT_PLATFORM_SRC"; \
	if [ "$$(uname -s)" = "Darwin" ]; then \
		QT_LIB_SRC="$$( $(VENV_PY) -c 'import PyQt5; from pathlib import Path; print((Path(PyQt5.__file__).resolve().parent / "Qt5" / "lib").as_posix())' )"; \
		QT_RUNTIME_DIR="$(PWD)/qt_runtime"; \
		mkdir -p "$$QT_RUNTIME_DIR/plugins/platforms"; \
		cp "$$QT_PLATFORM_SRC"/*.dylib "$$QT_RUNTIME_DIR/plugins/platforms/" 2>/dev/null || true; \
		ln -sfn "$$QT_LIB_SRC" "$$QT_RUNTIME_DIR/lib"; \
		QT_PLUGIN_PATH_RUN="$$QT_RUNTIME_DIR/plugins"; \
		QT_QPA_PLATFORM_PLUGIN_PATH_RUN="$$QT_RUNTIME_DIR/plugins/platforms"; \
	fi; \
	env -u PYTHONPATH -u PYTHONHOME QT_PLUGIN_PATH="$$QT_PLUGIN_PATH_RUN" QT_QPA_PLATFORM_PLUGIN_PATH="$$QT_QPA_PLATFORM_PLUGIN_PATH_RUN" $(VENV_PY) systemMonitor.py $(APP_ARGS) > $(LOG_FILE) 2>&1 & echo $$! > $(PID_FILE); \
	sleep 1; \
	if kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Started System Monitor with PID $$(cat $(PID_FILE)). Logs: $(LOG_FILE)"; \
	else \
		echo "System Monitor failed to start. Last log lines:"; \
		tail -n 20 $(LOG_FILE) || true; \
		rm -f $(PID_FILE); \
		exit 1; \
	fi

close:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		kill $$(cat $(PID_FILE)); \
		rm -f $(PID_FILE); \
		echo "Stopped System Monitor."; \
	else \
		echo "No managed app process is running."; \
		rm -f $(PID_FILE); \
	fi

status:
	@if [ -f $(PID_FILE) ] && kill -0 $$(cat $(PID_FILE)) 2>/dev/null; then \
		echo "Running (PID $$(cat $(PID_FILE)))."; \
	else \
		echo "Not running."; \
	fi
