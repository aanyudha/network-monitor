from __future__ import annotations

from pathlib import Path

from app.core.database.connection import DatabaseManager
from app.core.database.seed import seed_example_devices
from app.core.event_bus.bus import EventBus
from app.core.logging.setup import configure_logging
from app.core.notifications.service import NotificationService
from app.core.settings.service import SettingsService
from app.engines.alert.engine import AlertEngine
from app.engines.heartbeat.engine import HeartbeatEngine
from app.engines.http_check.engine import HttpCheckEngine
from app.engines.network_discovery.engine import NetworkDiscoveryEngine
from app.engines.port_check.engine import PortCheckEngine
from app.engines.reporting.engine import ReportingEngine
from app.engines.snmp_monitor.engine import SnmpMonitorEngine
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.dashboard.service import DashboardService
from app.modules.devices.actions import DeviceActions
from app.modules.devices.repository import DeviceRepository
from app.modules.devices.service import DeviceService
from app.modules.monitoring.service import MonitoringService
from app.modules.reports.service import ReportingService
from app.ui.main_window import MainWindow


def bootstrap_application():
    configure_logging()

    root = Path(__file__).resolve().parent.parent
    database_path = root / "app" / "data" / "heisenberg_monitor.db"
    database_manager = DatabaseManager(database_path)
    database_manager.initialize()

    connection_factory = database_manager.connect
    event_bus = EventBus()
    notifications = NotificationService()
    settings_service = SettingsService(connection_factory)

    device_repository = DeviceRepository(connection_factory)
    device_service = DeviceService(device_repository)
    alert_repository = AlertRepository(connection_factory)
    alert_service = AlertService(alert_repository, event_bus, notifications)
    dashboard_service = DashboardService(connection_factory, alert_service)

    heartbeat_engine = HeartbeatEngine()
    port_engine = PortCheckEngine()
    http_engine = HttpCheckEngine()
    alert_engine = AlertEngine()
    discovery_engine = NetworkDiscoveryEngine(heartbeat_engine)
    reporting_engine = ReportingEngine()
    snmp_engine = SnmpMonitorEngine()

    monitoring_service = MonitoringService(
        connection_factory=connection_factory,
        device_repository=device_repository,
        dashboard_service=dashboard_service,
        alert_service=alert_service,
        event_bus=event_bus,
        notifications=notifications,
        heartbeat_engine=heartbeat_engine,
        port_engine=port_engine,
        http_engine=http_engine,
        alert_engine=alert_engine,
        discovery_engine=discovery_engine,
        settings_service=settings_service,
    )
    reporting_service = ReportingService(connection_factory, reporting_engine)
    device_actions = DeviceActions(device_service, event_bus)

    seed_example_devices(device_service)

    window = MainWindow(
        device_service=device_service,
        device_actions=device_actions,
        dashboard_service=dashboard_service,
        alert_service=alert_service,
        monitoring_service=monitoring_service,
        reporting_service=reporting_service,
        settings_service=settings_service,
        notifications=notifications,
        snmp_engine=snmp_engine,
    )

    return {
        "window": window,
        "services": {
            "device_service": device_service,
            "dashboard_service": dashboard_service,
            "monitoring_service": monitoring_service,
            "reporting_service": reporting_service,
        },
    }

