from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from app.core.models import DEVICE_TYPES


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
    def __init__(self, monitoring_service, discovery_actions, snmp_engine) -> None:
        super().__init__()
        self._monitoring_service = monitoring_service
        self._discovery_actions = discovery_actions
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
        self.import_button = QPushButton("Save selected devices")
        toolbar.addWidget(self.subnet_edit)
        toolbar.addWidget(self.scan_button)
        toolbar.addWidget(self.import_button)

        note = QLabel(
            "Discovered devices are auto-classified with best-effort fingerprinting before import. "
            "Review and adjust types before saving.\n"
            + self._snmp_engine.status_message()
        )
        note.setProperty("muted", True)
        note.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Save", "IP", "Hostname", "Detected type", "Confidence", "Discovery notes", "Status", "Manual lock"]
        )
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
        self._results = self._discovery_actions.review(list(results))
        self.table.setRowCount(len(self._results))

        editable_types = [device_type for device_type in DEVICE_TYPES if device_type != "Database"]
        for row_index, item in enumerate(self._results):
            select_check = QCheckBox()
            select_check.setChecked(not item.is_existing_device)
            type_combo = QComboBox()
            type_combo.addItems(editable_types)
            type_combo.setCurrentText(item.device_type if item.device_type in editable_types else "Unknown")
            lock_check = QCheckBox()

            self.table.setCellWidget(row_index, 0, select_check)
            self.table.setItem(row_index, 1, QTableWidgetItem(item.ip_address))
            self.table.setItem(row_index, 2, QTableWidgetItem(item.hostname or "-"))
            self.table.setCellWidget(row_index, 3, type_combo)
            self.table.setItem(row_index, 4, QTableWidgetItem(f"{item.device_type_confidence}%"))
            self.table.setItem(row_index, 5, QTableWidgetItem(item.discovery_notes or "-"))
            self.table.setItem(row_index, 6, QTableWidgetItem(item.status))
            self.table.setCellWidget(row_index, 7, lock_check)

    def _handle_error(self, message: str) -> None:
        QMessageBox.warning(self, "Discovery failed", message)

    def import_results(self) -> None:
        selections = []
        for row_index, result in enumerate(self._results):
            save_widget = self.table.cellWidget(row_index, 0)
            type_widget = self.table.cellWidget(row_index, 3)
            lock_widget = self.table.cellWidget(row_index, 7)
            if isinstance(save_widget, QCheckBox) and save_widget.isChecked():
                selections.append(
                    {
                        "result": result,
                        "selected_type": type_widget.currentText() if isinstance(type_widget, QComboBox) else result.device_type,
                        "lock_type": lock_widget.isChecked() if isinstance(lock_widget, QCheckBox) else False,
                    }
                )

        if not selections:
            QMessageBox.information(self, "No devices selected", "Choose one or more discovery results to save.")
            return

        summary = self._discovery_actions.import_selected(selections)
        QMessageBox.information(
            self,
            "Discovery import",
            f"Created {summary['created']} devices, updated {summary['updated']} devices, skipped {summary['skipped']}.",
        )
