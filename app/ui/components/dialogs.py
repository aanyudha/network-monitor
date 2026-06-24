from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QLabel,
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
        self.lock_type_check = QCheckBox("Lock device type as manual override")
        self.lock_type_check.setChecked(device.device_type_locked if device else False)
        self.confidence_label = QLabel(
            f"{device.device_type_confidence}% confidence" if device and device.device_type_confidence else "No discovery confidence"
        )
        self.notes_label = QLabel(device.discovery_notes if device and device.discovery_notes else "No discovery notes")
        self.notes_label.setWordWrap(True)
        self.notes_label.setProperty("muted", True)

        form.addRow("Name", self.name_edit)
        form.addRow("IP address", self.ip_edit)
        form.addRow("Device type", self.type_combo)
        form.addRow("Discovery confidence", self.confidence_label)
        form.addRow("Discovery notes", self.notes_label)
        form.addRow("Location", self.location_edit)
        form.addRow("Monitoring profile", self.profile_edit)
        form.addRow("Custom ports", self.ports_edit)
        form.addRow("HTTP URL", self.http_url_edit)
        form.addRow("HTTP keyword", self.http_keyword_edit)
        form.addRow("Latency warning ms", self.latency_spin)
        form.addRow("", self.lock_type_check)
        form.addRow("", self.enabled_check)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addLayout(form)
        layout.addWidget(buttons)
        self._device_id = device.id if device else None
        self._original_type = device.device_type if device else ""
        self._original_confidence = device.device_type_confidence if device else 0
        self._original_notes = device.discovery_notes if device else ""

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
            device_type_confidence=self._original_confidence,
            discovery_notes=self._original_notes,
            device_type_locked=self.lock_type_check.isChecked() or self.type_combo.currentText() != self._original_type,
            location=self.location_edit.text().strip(),
            monitoring_profile=self.profile_edit.text().strip() or "standard",
            enabled=self.enabled_check.isChecked(),
            custom_ports=ports,
            http_url=self.http_url_edit.text().strip(),
            http_keyword=self.http_keyword_edit.text().strip(),
            latency_warning_ms=self.latency_spin.value(),
        )
