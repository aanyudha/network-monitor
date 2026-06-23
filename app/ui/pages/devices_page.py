from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.dialogs import DeviceDialog


class DevicesPage(QWidget):
    def __init__(self, device_service, device_actions) -> None:
        super().__init__()
        self._device_service = device_service
        self._device_actions = device_actions

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

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "IP", "Type", "Location", "Ports", "HTTP URL", "Enabled"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        panel_layout.addWidget(self.table)

        layout.addLayout(toolbar)
        layout.addWidget(panel)

        self.add_button.clicked.connect(self._add_device)
        self.edit_button.clicked.connect(self._edit_device)
        self.delete_button.clicked.connect(self._delete_device)
        self.refresh_button.clicked.connect(self.load_devices)

    def load_devices(self) -> None:
        devices = self._device_service.list_devices()
        self.table.setRowCount(len(devices))
        for row_index, device in enumerate(devices):
            values = [
                device.id,
                device.name,
                device.ip_address,
                device.device_type,
                device.location,
                ", ".join(str(port) for port in device.custom_ports),
                device.http_url,
                "Yes" if device.enabled else "No",
            ]
            for column_index, value in enumerate(values):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

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

