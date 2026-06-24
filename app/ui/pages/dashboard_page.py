from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.cards import SectionHeader, SummaryCard
from app.ui.components.status_badge import StatusBadge


class DashboardPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)
        self.total_card = SummaryCard("Total devices", "#7fc8ff")
        self.online_card = SummaryCard("Online", "#33c27f")
        self.offline_card = SummaryCard("Offline", "#ff6577")
        self.warning_card = SummaryCard("Warning", "#ffbf47")
        self.latency_card = SummaryCard("Avg latency", "#9f93ff")

        cards = [self.total_card, self.online_card, self.offline_card, self.warning_card, self.latency_card]
        for index, card in enumerate(cards):
            cards_layout.addWidget(card, 0, index)

        health_panel = QFrame()
        health_panel.setObjectName("panel")
        health_layout = QVBoxLayout(health_panel)
        health_layout.addWidget(SectionHeader("Network health"))
        self.health_label = QLabel("0.0%")
        self.health_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.health_bar = QProgressBar()
        self.health_bar.setRange(0, 100)
        health_layout.addWidget(self.health_label)
        health_layout.addWidget(self.health_bar)

        tables_layout = QGridLayout()
        tables_layout.setSpacing(16)

        status_panel = QFrame()
        status_panel.setObjectName("panel")
        status_layout = QVBoxLayout(status_panel)
        status_layout.addWidget(SectionHeader("Realtime status"))
        self.status_table = QTableWidget(0, 7)
        self.status_table.setHorizontalHeaderLabels(
            ["Device", "IP", "Type", "Status", "Latency", "Ports", "Last checked"]
        )
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.status_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        status_layout.addWidget(self.status_table)

        alerts_panel = QFrame()
        alerts_panel.setObjectName("panel")
        alerts_layout = QVBoxLayout(alerts_panel)
        alerts_layout.addWidget(SectionHeader("Recent alerts"))
        self.alerts_list = QListWidget()
        alerts_layout.addWidget(self.alerts_list)

        tables_layout.addWidget(status_panel, 0, 0, 1, 2)
        tables_layout.addWidget(alerts_panel, 0, 2)

        layout.addLayout(cards_layout)
        layout.addWidget(health_panel)
        layout.addLayout(tables_layout)

    def refresh(self, summary) -> None:
        self.total_card.set_value(str(summary.total_devices))
        self.online_card.set_value(str(summary.online_devices))
        self.offline_card.set_value(str(summary.offline_devices))
        self.warning_card.set_value(str(summary.warning_devices))
        self.latency_card.set_value(f"{summary.average_latency_ms:.1f} ms")
        self.health_label.setText(f"{summary.network_health_percent:.1f}%")
        self.health_bar.setValue(int(summary.network_health_percent))

        self.status_table.setRowCount(len(summary.status_rows))
        for row_index, row in enumerate(summary.status_rows):
            values = [
                row["name"],
                row["ip_address"],
                row["device_type"],
                "-" if row["latency_ms"] is None else f'{row["latency_ms"]:.1f} ms',
                row["open_ports"] or "-",
                row["checked_at"],
            ]
            for column_index, value in enumerate(values):
                target_column = column_index if column_index < 3 else column_index + 1
                self.status_table.setItem(row_index, target_column, QTableWidgetItem(str(value)))
            self.status_table.setCellWidget(
                row_index,
                3,
                StatusBadge(row["status"], enabled=bool(row["enabled"])),
            )

        self.alerts_list.clear()
        for alert in summary.recent_alerts:
            item = QListWidgetItem(f"[{alert.severity.upper()}] {alert.message} ({alert.created_at})")
            self.alerts_list.addItem(item)
