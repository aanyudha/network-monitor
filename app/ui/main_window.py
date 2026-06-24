from __future__ import annotations

import asyncio

from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.alerts_page import AlertsPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.devices_page import DevicesPage
from app.ui.pages.network_page import NetworkPage
from app.ui.pages.reports_page import ReportsPage
from app.ui.themes.palette import build_stylesheet


class MonitoringWorker(QObject):
    summary_ready = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, monitoring_service, polling_interval: int) -> None:
        super().__init__()
        self._monitoring_service = monitoring_service
        self._polling_interval = polling_interval
        self._stop_requested = False

    def stop(self) -> None:
        self._stop_requested = True

    @Slot()
    def run(self) -> None:
        try:
            asyncio.run(self._loop())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()

    async def _loop(self) -> None:
        while not self._stop_requested:
            summary = await self._monitoring_service.poll_cycle()
            self.summary_ready.emit(summary)
            await asyncio.sleep(self._polling_interval)


class MainWindow(QMainWindow):
    def __init__(
        self,
        device_service,
        device_actions,
        discovery_actions,
        dashboard_service,
        alert_service,
        monitoring_service,
        reporting_service,
        settings_service,
        notifications,
        snmp_engine,
        import_dns_log_action,
        import_firewall_log_action,
        list_device_traffic_action,
    ) -> None:
        super().__init__()
        self._dashboard_service = dashboard_service
        self._monitoring_service = monitoring_service
        self._reporting_service = reporting_service
        self._settings_service = settings_service
        self._notifications = notifications
        self._theme_mode = str(self._settings_service.get("theme_mode"))

        self._monitoring_thread = None
        self._monitoring_worker = None

        self.setWindowTitle("Heisenberg Network Monitor")
        self.resize(1440, 920)
        self.setStyleSheet(build_stylesheet(self._theme_mode))

        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(12)

        title = QLabel("Heisenberg\nNetwork Monitor")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        subtitle = QLabel("Agentless heartbeat and network health")
        subtitle.setProperty("muted", True)
        subtitle.setWordWrap(True)
        sidebar_layout.addWidget(title)
        sidebar_layout.addWidget(subtitle)

        self.nav_buttons = []
        nav_items = ["Dashboard", "Devices", "Alerts", "Reports", "Discovery"]
        for name in nav_items:
            button = QPushButton(name)
            button.setCheckable(True)
            sidebar_layout.addWidget(button)
            self.nav_buttons.append(button)
        sidebar_layout.addStretch()

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(16)

        toolbar = QHBoxLayout()
        self.start_button = QPushButton("Start monitoring")
        self.start_button.setProperty("accent", True)
        self.stop_button = QPushButton("Stop")
        self.theme_button = QPushButton("Toggle theme")
        self.refresh_button = QPushButton("Refresh now")
        toolbar.addWidget(self.start_button)
        toolbar.addWidget(self.stop_button)
        toolbar.addWidget(self.theme_button)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_button)

        self.stack = QStackedWidget()
        self.dashboard_page = DashboardPage()
        self.devices_page = DevicesPage(
            device_service,
            device_actions,
            dashboard_service,
            import_dns_log_action,
            import_firewall_log_action,
            list_device_traffic_action,
        )
        self.alerts_page = AlertsPage(alert_service, dashboard_service)
        self.reports_page = ReportsPage(reporting_service)
        self.network_page = NetworkPage(monitoring_service, discovery_actions, snmp_engine)
        for page in [
            self.dashboard_page,
            self.devices_page,
            self.alerts_page,
            self.reports_page,
            self.network_page,
        ]:
            self.stack.addWidget(page)

        content_layout.addLayout(toolbar)
        content_layout.addWidget(self.stack)

        root_layout.addWidget(sidebar, 0)
        root_layout.addWidget(content, 1)
        self.setCentralWidget(root)
        self.setStatusBar(QStatusBar())

        for index, button in enumerate(self.nav_buttons):
            button.clicked.connect(lambda checked=False, idx=index: self._switch_page(idx))
        self.nav_buttons[0].setChecked(True)

        self.start_button.clicked.connect(self.start_monitoring)
        self.stop_button.clicked.connect(self.stop_monitoring)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.refresh_button.clicked.connect(self.refresh_all)
        self._notifications.subscribe(self._show_notification)

        self.refresh_all()

    def _switch_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for button_index, button in enumerate(self.nav_buttons):
            button.setChecked(button_index == index)

    def refresh_all(self) -> None:
        summary = self._dashboard_service.build_summary()
        self.dashboard_page.refresh(summary)
        self.devices_page.load_devices()
        self.alerts_page.load_alerts()
        self.reports_page.load_report()

    def start_monitoring(self) -> None:
        if self._monitoring_thread and self._monitoring_thread.isRunning():
            return
        self.statusBar().showMessage("Monitoring started")
        self._monitoring_thread = QThread(self)
        interval = int(self._settings_service.get("polling_interval_seconds"))
        self._monitoring_worker = MonitoringWorker(self._monitoring_service, interval)
        self._monitoring_worker.moveToThread(self._monitoring_thread)
        self._monitoring_thread.started.connect(self._monitoring_worker.run)
        self._monitoring_worker.summary_ready.connect(self._handle_summary)
        self._monitoring_worker.failed.connect(self._handle_monitoring_error)
        self._monitoring_worker.finished.connect(self._monitoring_thread.quit)
        self._monitoring_thread.start()

    def stop_monitoring(self) -> None:
        if self._monitoring_worker:
            self._monitoring_worker.stop()
        self.statusBar().showMessage("Monitoring stopping")

    def toggle_theme(self) -> None:
        self._theme_mode = "light" if self._theme_mode == "dark" else "dark"
        self._settings_service.set("theme_mode", self._theme_mode)
        self.setStyleSheet(build_stylesheet(self._theme_mode))

    def _handle_summary(self, summary) -> None:
        self.dashboard_page.refresh(summary)
        self.alerts_page.load_alerts()
        self.reports_page.load_report()
        self.statusBar().showMessage(f"Monitoring cycle completed at {summary.status_rows[0]['checked_at']}" if summary.status_rows else "Monitoring cycle completed")

    def _handle_monitoring_error(self, message: str) -> None:
        QMessageBox.warning(self, "Monitoring error", message)
        self.statusBar().showMessage("Monitoring error")

    def _show_notification(self, title: str, message: str) -> None:
        self.statusBar().showMessage(f"{title}: {message}", 8000)
