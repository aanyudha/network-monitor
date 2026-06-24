from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.core.status import status_meta


class StatusBadge(QWidget):
    def __init__(self, status: str, enabled: bool = True, parent=None) -> None:
        super().__init__(parent)
        meta = status_meta(status, enabled)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)

        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {meta['dot']}; border-radius: 5px;")
        dot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(meta["label"])
        label.setStyleSheet(f"color: {meta['color']}; font-weight: 600;")

        layout.addWidget(dot)
        layout.addWidget(label)
        layout.addStretch()
