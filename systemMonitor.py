"""Backward-compatible launcher for the packaged app."""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from system_monitor.app import main


if __name__ == "__main__":
    raise SystemExit(main())
