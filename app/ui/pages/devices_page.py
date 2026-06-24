from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.dialogs import DeviceDialog
from app.ui.components.status_badge import StatusBadge


class DevicesPage(QWidget):
    def __init__(
        self,
        device_service,
        device_actions,
        dashboard_service,
        import_dns_log_action,
        import_firewall_log_action,
        list_device_traffic_action,
    ) -> None:
        super().__init__()
        self._device_service = device_service
        self._device_actions = device_actions
        self._dashboard_service = dashboard_service
        self._import_dns_log_action = import_dns_log_action
        self._import_firewall_log_action = import_firewall_log_action
        self._list_device_traffic_action = list_device_traffic_action

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.add_button = QPushButton("Add device")
        self.add_button.setProperty("accent", True)
        self.edit_button = QPushButton("Edit")
        self.delete_button = QPushButton("Delete")
        self.refresh_button = QPushButton("Refresh")
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_button)

        table_panel = QFrame()
        table_panel.setObjectName("panel")
        table_layout = QVBoxLayout(table_panel)
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "IP", "Type", "Confidence", "Locked", "Status", "Location", "Ports", "Enabled"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table_layout.addWidget(self.table)

        detail_panel = QFrame()
        detail_panel.setObjectName("panel")
        detail_layout = QVBoxLayout(detail_panel)

        detail_header = QHBoxLayout()
        detail_title = QLabel("Traffic Visibility")
        detail_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.import_dns_button = QPushButton("Import DNS CSV")
        self.import_firewall_button = QPushButton("Import firewall CSV")
        detail_header.addWidget(detail_title)
        detail_header.addStretch()
        detail_header.addWidget(self.import_dns_button)
        detail_header.addWidget(self.import_firewall_button)

        self.visibility_note = QLabel(
            "Traffic visibility requires DNS/firewall/proxy/NetFlow logs. "
            "Agentless IP discovery alone cannot see per-PC browsing destinations."
        )
        self.visibility_note.setWordWrap(True)
        self.visibility_note.setProperty("muted", True)

        self.summary_label = QLabel("Select a device to review imported traffic observations.")
        self.summary_label.setWordWrap(True)

        self.traffic_table = QTableWidget(0, 6)
        self.traffic_table.setHorizontalHeaderLabels(
            ["Observed", "Domain", "Destination IP", "Public IP", "Protocol/Port", "Source"]
        )
        self.traffic_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.traffic_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        detail_layout.addLayout(detail_header)
        detail_layout.addWidget(self.visibility_note)
        detail_layout.addWidget(self.summary_label)
        detail_layout.addWidget(self.traffic_table)

        layout.addLayout(toolbar)
        layout.addWidget(table_panel)
        layout.addWidget(detail_panel)

        self.add_button.clicked.connect(self._add_device)
        self.edit_button.clicked.connect(self._edit_device)
        self.delete_button.clicked.connect(self._delete_device)
        self.refresh_button.clicked.connect(self.load_devices)
        self.import_dns_button.clicked.connect(lambda: self._import_traffic_log(self._import_dns_log_action, "DNS"))
        self.import_firewall_button.clicked.connect(
            lambda: self._import_traffic_log(self._import_firewall_log_action, "firewall")
        )
        self.table.itemSelectionChanged.connect(self._refresh_traffic_panel)

    def load_devices(self) -> None:
        devices = self._device_service.list_devices()
        summary = self._dashboard_service.build_summary()
        status_by_device = {row["device_id"]: row for row in summary.status_rows}

        self.table.setRowCount(len(devices))
        for row_index, device in enumerate(devices):
            status_row = status_by_device.get(device.id, {"status": "Unknown", "enabled": device.enabled})
            values = [
                device.id,
                device.name,
                device.ip_address,
                device.device_type,
                f"{device.device_type_confidence}%",
                "Yes" if device.device_type_locked else "No",
                device.location,
                ", ".join(str(port) for port in device.custom_ports),
                "Yes" if device.enabled else "No",
            ]
            for column_index, value in enumerate(values):
                target_column = column_index if column_index < 6 else column_index + 1
                self.table.setItem(row_index, target_column, QTableWidgetItem(str(value)))
            self.table.setCellWidget(
                row_index,
                6,
                StatusBadge(status_row["status"], enabled=bool(status_row["enabled"])),
            )

        if devices and self.table.currentRow() < 0:
            self.table.selectRow(0)
        elif not devices:
            self._refresh_traffic_panel()

    def _selected_device_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    def _add_device(self) -> None:
        dialog = DeviceDialog(self)
        if dialog.exec():
            try:
                self._device_actions.create(dialog.to_device())
                self.load_devices()
            except ValueError as exc:
                QMessageBox.warning(self, "Could not add device", str(exc))

    def _edit_device(self) -> None:
        device_id = self._selected_device_id()
        if device_id is None:
            QMessageBox.information(self, "Select device", "Choose a device to edit.")
            return
        device = self._device_service.get_device(device_id)
        if device is None:
            return
        dialog = DeviceDialog(self, device)
        if dialog.exec():
            try:
                self._device_actions.update(dialog.to_device())
                self.load_devices()
            except ValueError as exc:
                QMessageBox.warning(self, "Could not update device", str(exc))

    def _delete_device(self) -> None:
        device_id = self._selected_device_id()
        if device_id is None:
            QMessageBox.information(self, "Select device", "Choose a device to delete.")
            return
        if QMessageBox.question(self, "Delete device", "Delete the selected device?") == QMessageBox.StandardButton.Yes:
            self._device_actions.delete(device_id)
            self.load_devices()

    def _import_traffic_log(self, action, label: str) -> None:
        path_text, _ = QFileDialog.getOpenFileName(self, f"Import {label} CSV", "", "CSV Files (*.csv)")
        if not path_text:
            return
        try:
            imported = action.run(Path(path_text))
            QMessageBox.information(self, "Traffic import", f"Imported {imported} {label.lower()} observations.")
            self._refresh_traffic_panel()
        except ValueError as exc:
            QMessageBox.warning(self, "Traffic import failed", str(exc))

    def _refresh_traffic_panel(self) -> None:
        device_id = self._selected_device_id()
        if device_id is None:
            self.summary_label.setText("Select a device to review imported traffic observations.")
            self.traffic_table.setRowCount(0)
            return

        traffic = self._list_device_traffic_action.run(device_id)
        domains = ", ".join(traffic["recent_domains"]) or "-"
        public_ips = ", ".join(traffic["recent_public_ips"]) or "-"
        ports = ", ".join(traffic["destination_ports"]) or "-"
        self.summary_label.setText(
            f"Recent domains: {domains}\n"
            f"Recent public IPs: {public_ips}\n"
            f"Destination ports: {ports}\n"
            f"Last observed: {traffic['last_observed']}"
        )

        rows = traffic["rows"]
        self.traffic_table.setRowCount(len(rows))
        for row_index, observation in enumerate(rows):
            values = [
                observation.observed_at,
                observation.domain or "-",
                observation.destination_ip or "-",
                observation.public_ip or "-",
                f"{observation.protocol or '-'} / {observation.port or '-'}",
                observation.source_type,
            ]
            for column_index, value in enumerate(values):
                self.traffic_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))
