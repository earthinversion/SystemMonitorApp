from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile

import PyQt5
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication

from system_monitor.services.csv_exporter import CsvMetricsExporter
from system_monitor.services.system_stats import SystemStatsService
from system_monitor.ui.main_window import MainWindow
from system_monitor.ui.splash_screen import SplashScreen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Desktop system monitor")
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=1000,
        help="Sampling interval in milliseconds (default: 1000)",
    )
    parser.add_argument(
        "--history-seconds",
        type=int,
        default=30,
        help="Visible history window in seconds (default: 30)",
    )
    parser.add_argument(
        "--export-csv",
        type=Path,
        help="Write captured metrics to a CSV file.",
    )
    parser.add_argument(
        "--no-splash",
        action="store_true",
        help="Start directly with the dashboard window.",
    )
    parser.add_argument(
        "--start-maximized",
        action="store_true",
        help="Open the dashboard in maximized mode.",
    )
    return parser


def configure_qt_plugin_paths() -> None:
    plugin_root = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
    platform_root = plugin_root / "platforms"
    if not platform_root.exists():
        return

    effective_plugin_root = plugin_root
    effective_platform_root = platform_root

    # On macOS, Qt can fail to discover plugins when they're under a hidden path (like `.venv`).
    # I stage platform plugins into a visible runtime path so the Cocoa plugin can be loaded reliably.
    if sys.platform == "darwin" and any(part.startswith(".") for part in plugin_root.parts):
        runtime_root = Path(tempfile.gettempdir()) / "system-monitor-qt-runtime"
        runtime_plugin_root = runtime_root / "plugins"
        runtime_platform_root = runtime_plugin_root / "platforms"
        runtime_platform_root.mkdir(parents=True, exist_ok=True)

        for dylib in platform_root.glob("*.dylib"):
            shutil.copy2(dylib, runtime_platform_root / dylib.name)

        qt_lib_root = plugin_root.parent / "lib"
        runtime_lib_link = runtime_root / "lib"
        if qt_lib_root.exists():
            if runtime_lib_link.exists() or runtime_lib_link.is_symlink():
                if runtime_lib_link.is_symlink() and runtime_lib_link.resolve() == qt_lib_root.resolve():
                    pass
                elif runtime_lib_link.is_symlink() or runtime_lib_link.is_file():
                    runtime_lib_link.unlink()
                else:
                    shutil.rmtree(runtime_lib_link)
            if not runtime_lib_link.exists():
                runtime_lib_link.symlink_to(qt_lib_root, target_is_directory=True)

        effective_plugin_root = runtime_plugin_root
        effective_platform_root = runtime_platform_root

    if not os.environ.get("QT_PLUGIN_PATH", "").strip():
        os.environ["QT_PLUGIN_PATH"] = str(effective_plugin_root)
    if not os.environ.get("QT_QPA_PLATFORM_PLUGIN_PATH", "").strip():
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(effective_platform_root)
    QtCore.QCoreApplication.addLibraryPath(str(effective_plugin_root))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_qt_plugin_paths()

    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    stats_service = SystemStatsService()
    exporter = CsvMetricsExporter(args.export_csv) if args.export_csv else None

    def create_main_window() -> MainWindow:
        return MainWindow(
            stats_service=stats_service,
            history_seconds=args.history_seconds,
            poll_interval_ms=args.interval_ms,
            exporter=exporter,
            start_maximized=args.start_maximized,
        )

    if args.no_splash:
        window = create_main_window()
        if args.start_maximized:
            window.showMaximized()
        else:
            window.show()
        return app.exec_()

    splash = SplashScreen(window_factory=create_main_window)
    splash.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
