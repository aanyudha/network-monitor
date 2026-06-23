from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

from app.core.models import DEVICE_TYPES, Device


class DeviceDialog(QDialog):
    def __init__(self, parent=None, device: Device | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Device")
        self.resize(420, 360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(device.name if device else "")
        self.ip_edit = QLineEdit(device.ip_address if device else "")
        self.type_combo = QComboBox()
        self.type_combo.addItems(DEVICE_TYPES)
        self.type_combo.setCurrentText(device.device_type if device else "Other")
        self.location_edit = QLineEdit(device.location if device else "")
        self.profile_edit = QLineEdit(device.monitoring_profile if device else "standard")
        self.ports_edit = QLineEdit(",".join(str(port) for port in device.custom_ports) if device else "")
        self.http_url_edit = QLineEdit(device.http_url if device else "")
        self.http_keyword_edit = QLineEdit(device.http_keyword if device else "")
        self.latency_spin = QSpinBox()
        self.latency_spin.setRange(1, 5000)
        self.latency_spin.setValue(device.latency_warning_ms if device else 250)
        self.enabled_check = QCheckBox("Enabled")
        self.enabled_check.setChecked(device.enabled if device else True)

        form.addRow("Name", self.name_edit)
        form.addRow("IP address", self.ip_edit)
        form.addRow("Device type", self.type_combo)
        form.addRow("Location", self.location_edit)
        form.addRow("Monitoring profile", self.profile_edit)
        form.addRow("Custom ports", self.ports_edit)
        form.addRow("HTTP URL", self.http_url_edit)
        form.addRow("HTTP keyword", self.http_keyword_edit)
        form.addRow("Latency warning ms", self.latency_spin)
        form.addRow("", self.enabled_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)
        self._device_id = device.id if device else None

    def accept(self) -> None:
        try:
            self.to_device()
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid device", str(exc))
            return
        super().accept()

    def to_device(self) -> Device:
        ports = []
        if self.ports_edit.text().strip():
            try:
                ports = [int(part.strip()) for part in self.ports_edit.text().split(",") if part.strip()]
            except ValueError as exc:
                raise ValueError("Ports must be comma-separated numbers.") from exc

        return Device(
            id=self._device_id,
            name=self.name_edit.text().strip(),
            ip_address=self.ip_edit.text().strip(),
            device_type=self.type_combo.currentText(),
            location=self.location_edit.text().strip(),
            monitoring_profile=self.profile_edit.text().strip() or "standard",
            enabled=self.enabled_check.isChecked(),
            custom_ports=ports,
            http_url=self.http_url_edit.text().strip(),
            http_keyword=self.http_keyword_edit.text().strip(),
            latency_warning_ms=self.latency_spin.value(),
        )

