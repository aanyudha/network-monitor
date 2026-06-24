from __future__ import annotations

import argparse
import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import bootstrap_application, build_service_container


def main() -> int:
    parser = argparse.ArgumentParser(description="Heisenberg Network Monitor")
    parser.add_argument("--smoke", action="store_true", help="Import and bootstrap services without launching the UI.")
    args = parser.parse_args()

    if args.smoke:
        build_service_container()
        return 0

    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Heisenberg Network Monitor")
    qt_app.setOrganizationName("Heisenberg Network Monitor")
    container = bootstrap_application()
    window = container["window"]
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
