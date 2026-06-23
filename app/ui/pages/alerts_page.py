from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class AlertsPage(QWidget):
    def __init__(self, alert_service) -> None:
        super().__init__()
        self._alert_service = alert_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Status", "Device ID", "Message"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        panel_layout.addWidget(self.table)

        layout.addWidget(panel)

    def load_alerts(self) -> None:
        alerts = self._alert_service.all_alerts()
        self.table.setRowCount(len(alerts))
        for row_index, alert in enumerate(alerts):
            values = [alert.created_at, alert.alert_type, alert.severity, alert.status, alert.device_id, alert.message]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

