from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.core.models import Device


class DiscoveryWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, monitoring_service, subnet: str) -> None:
        super().__init__()
        self._monitoring_service = monitoring_service
        self._subnet = subnet

    @Slot()
    def run(self) -> None:
        try:
            results = asyncio.run(self._monitoring_service.discover_devices(self._subnet))
            self.completed.emit(results)
        except Exception as exc:
            self.failed.emit(str(exc))


class NetworkPage(QWidget):
    def __init__(self, monitoring_service, device_actions, snmp_engine) -> None:
        super().__init__()
        self._monitoring_service = monitoring_service
        self._device_actions = device_actions
        self._snmp_engine = snmp_engine
        self._results = []
        self._thread = None
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.subnet_edit = QLineEdit("192.168.1.0/24")
        self.scan_button = QPushButton("Scan subnet")
        self.import_button = QPushButton("Import discovered")
        toolbar.addWidget(self.subnet_edit)
        toolbar.addWidget(self.scan_button)
        toolbar.addWidget(self.import_button)

        note = QLabel(self._snmp_engine.status_message())
        note.setProperty("muted", True)
        note.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["IP", "Hostname", "Reachable"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        panel_layout.addWidget(self.table)

        layout.addLayout(toolbar)
        layout.addWidget(note)
        layout.addWidget(panel)

        self.scan_button.clicked.connect(self.start_scan)
        self.import_button.clicked.connect(self.import_results)

    def start_scan(self) -> None:
        self.scan_button.setEnabled(False)
        self._thread = QThread(self)
        self._worker = DiscoveryWorker(self._monitoring_service, self.subnet_edit.text().strip())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.completed.connect(self._handle_results)
        self._worker.failed.connect(self._handle_error)
        self._worker.completed.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(lambda: self.scan_button.setEnabled(True))
        self._thread.start()

    def _handle_results(self, results) -> None:
        self._results = list(results)
        self.table.setRowCount(len(self._results))
        for row_index, item in enumerate(self._results):
            values = [item.ip_address, item.hostname or "-", "Yes" if item.reachable else "No"]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def _handle_error(self, message: str) -> None:
        QMessageBox.warning(self, "Discovery failed", message)

    def import_results(self) -> None:
        created = 0
        for result in self._results:
            try:
                self._device_actions.create(
                    Device(
                        name=result.hostname or f"Discovered {result.ip_address}",
                        ip_address=result.ip_address,
                        device_type="Other",
                    )
                )
                created += 1
            except ValueError:
                continue
        QMessageBox.information(self, "Discovery import", f"Imported {created} devices.")

