from __future__ import annotations

from app.core.database.connection import DatabaseManager
from app.core.database.seed import seed_example_devices
from app.core.event_bus.bus import EventBus
from app.core.logging.setup import configure_logging
from app.core.notifications.service import NotificationService
from app.core.runtime.paths import runtime_database_path, runtime_exports_dir, runtime_logs_dir
from app.core.settings.service import SettingsService
from app.engines.alert.engine import AlertEngine
from app.engines.heartbeat.engine import HeartbeatEngine
from app.engines.http_check.engine import HttpCheckEngine
from app.engines.network_discovery.classification import DiscoveryClassificationEngine
from app.engines.network_discovery.engine import NetworkDiscoveryEngine
from app.engines.port_check.engine import PortCheckEngine
from app.engines.reporting.engine import ReportingEngine
from app.engines.snmp_monitor.engine import SnmpMonitorEngine
from app.engines.traffic_visibility.engine import TrafficVisibilityEngine
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.dashboard.service import DashboardService
from app.modules.discovery.actions import DiscoveryActions
from app.modules.discovery.service import DiscoveryService
from app.modules.devices.actions import DeviceActions
from app.modules.devices.repository import DeviceRepository
from app.modules.devices.service import DeviceService
from app.modules.monitoring.service import MonitoringService
from app.modules.reports.service import ReportingService
from app.modules.traffic_visibility.actions import ImportDnsLogAction, ImportFirewallLogAction, ListDeviceTrafficAction
from app.modules.traffic_visibility.repository import TrafficVisibilityRepository
from app.modules.traffic_visibility.service import TrafficVisibilityService
from app.ui.main_window import MainWindow


def build_service_container():
    configure_logging()
    runtime_logs_dir()
    runtime_exports_dir()

    database_manager = DatabaseManager(runtime_database_path())
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
    discovery_service = DiscoveryService(device_repository, device_service)

    heartbeat_engine = HeartbeatEngine()
    port_engine = PortCheckEngine()
    http_engine = HttpCheckEngine()
    alert_engine = AlertEngine()
    classification_engine = DiscoveryClassificationEngine()
    discovery_engine = NetworkDiscoveryEngine(heartbeat_engine, port_engine, classification_engine)
    reporting_engine = ReportingEngine()
    snmp_engine = SnmpMonitorEngine()
    traffic_engine = TrafficVisibilityEngine()

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
    discovery_actions = DiscoveryActions(discovery_service, event_bus)
    traffic_repository = TrafficVisibilityRepository(connection_factory)
    traffic_service = TrafficVisibilityService(device_repository, traffic_repository, traffic_engine)
    import_dns_log_action = ImportDnsLogAction(traffic_service)
    import_firewall_log_action = ImportFirewallLogAction(traffic_service)
    list_device_traffic_action = ListDeviceTrafficAction(traffic_service)

    seed_example_devices(device_service)

    return {
        "services": {
            "device_service": device_service,
            "dashboard_service": dashboard_service,
            "monitoring_service": monitoring_service,
            "reporting_service": reporting_service,
            "traffic_visibility_service": traffic_service,
        },
        "actions": {
            "device_actions": device_actions,
            "discovery_actions": discovery_actions,
            "import_dns_log_action": import_dns_log_action,
            "import_firewall_log_action": import_firewall_log_action,
            "list_device_traffic_action": list_device_traffic_action,
        },
        "engines": {
            "snmp_engine": snmp_engine,
        },
        "settings_service": settings_service,
        "notifications": notifications,
        "alert_service": alert_service,
    }


def bootstrap_application():
    container = build_service_container()
    window = MainWindow(
        device_service=container["services"]["device_service"],
        device_actions=container["actions"]["device_actions"],
        discovery_actions=container["actions"]["discovery_actions"],
        dashboard_service=container["services"]["dashboard_service"],
        alert_service=container["alert_service"],
        monitoring_service=container["services"]["monitoring_service"],
        reporting_service=container["services"]["reporting_service"],
        settings_service=container["settings_service"],
        notifications=container["notifications"],
        snmp_engine=container["engines"]["snmp_engine"],
        import_dns_log_action=container["actions"]["import_dns_log_action"],
        import_firewall_log_action=container["actions"]["import_firewall_log_action"],
        list_device_traffic_action=container["actions"]["list_device_traffic_action"],
    )

    container["window"] = window
    return container
