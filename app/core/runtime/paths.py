from __future__ import annotations

import os
import sys
from pathlib import Path


APP_DIR_NAME = "HeisenbergNetworkMonitor"


def application_root() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.getenv("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return base / APP_DIR_NAME
    return Path(__file__).resolve().parents[3]


def runtime_data_dir() -> Path:
    path = application_root() / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_logs_dir() -> Path:
    path = application_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_exports_dir() -> Path:
    path = application_root() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def runtime_database_path() -> Path:
    return runtime_data_dir() / "heisenberg_monitor.db"
