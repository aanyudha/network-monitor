from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHeaderView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from app.ui.components.status_badge import StatusBadge


class AlertsPage(QWidget):
    def __init__(self, alert_service, dashboard_service) -> None:
        super().__init__()
        self._alert_service = alert_service
        self._dashboard_service = dashboard_service

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Time", "Type", "Severity", "Alert", "Device ID", "Device status", "Message"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        panel_layout.addWidget(self.table)

        layout.addWidget(panel)

    def load_alerts(self) -> None:
        alerts = self._alert_service.all_alerts()
        summary = self._dashboard_service.build_summary()
        status_by_device = {row["device_id"]: row for row in summary.status_rows}
        self.table.setRowCount(len(alerts))
        for row_index, alert in enumerate(alerts):
            values = [alert.created_at, alert.alert_type, alert.severity, alert.status, alert.device_id, alert.message]
            for column_index, value in enumerate(values):
                target_column = column_index if column_index < 5 else column_index + 1
                self.table.setItem(row_index, target_column, QTableWidgetItem(str(value)))
            status_row = status_by_device.get(alert.device_id, {"status": "Unknown", "enabled": True})
            self.table.setCellWidget(
                row_index,
                5,
                StatusBadge(status_row["status"], enabled=bool(status_row["enabled"])),
            )
