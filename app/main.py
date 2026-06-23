from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.bootstrap import bootstrap_application


def main() -> int:
    qt_app = QApplication(sys.argv)
    qt_app.setApplicationName("Heisenberg Network Monitor")
    qt_app.setOrganizationName("Heisenberg Network Monitor")
    container = bootstrap_application()
    window = container["window"]
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

