from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ReportsPage(QWidget):
    def __init__(self, reporting_service) -> None:
        super().__init__()
        self._reporting_service = reporting_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(7)
        self.export_button = QPushButton("Export CSV")
        self.load_button = QPushButton("Refresh report")
        toolbar.addWidget(self.days_spin)
        toolbar.addWidget(self.load_button)
        toolbar.addStretch()
        toolbar.addWidget(self.export_button)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Name", "IP", "Checks", "Online", "Offline", "Availability %"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        panel_layout.addWidget(self.table)

        layout.addLayout(toolbar)
        layout.addWidget(panel)

        self.load_button.clicked.connect(self.load_report)
        self.export_button.clicked.connect(self.export_csv)

    def load_report(self) -> None:
        rows = self._reporting_service.availability_rows(self.days_spin.value())
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["name"],
                row["ip_address"],
                row["total_checks"],
                row["online_checks"],
                row["offline_checks"],
                row["availability_percent"],
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def export_csv(self) -> None:
        suggested = str(Path.cwd() / "exports" / "availability-report.csv")
        file_name, _ = QFileDialog.getSaveFileName(self, "Export report", suggested, "CSV Files (*.csv)")
        if not file_name:
            return
        exported = self._reporting_service.export_availability_csv(Path(file_name), self.days_spin.value())
        QMessageBox.information(self, "Export complete", f"Report exported to:\n{exported}")

