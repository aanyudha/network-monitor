from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database.connection import DatabaseManager
from app.core.event_bus.bus import EventBus
from app.core.notifications.service import NotificationService
from app.core.settings.service import SettingsService
from app.engines.alert.engine import AlertEngine
from app.engines.heartbeat.engine import HeartbeatEngine
from app.engines.http_check.engine import HttpCheckEngine
from app.engines.network_discovery.classification import DiscoveryClassificationEngine
from app.engines.network_discovery.engine import NetworkDiscoveryEngine
from app.engines.port_check.engine import PortCheckEngine
from app.engines.reporting.engine import ReportingEngine
from app.engines.traffic_visibility.engine import TrafficVisibilityEngine
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.service import AlertService
from app.modules.dashboard.service import DashboardService
from app.modules.devices.repository import DeviceRepository
from app.modules.devices.service import DeviceService
from app.modules.monitoring.service import MonitoringService
from app.modules.reports.service import ReportingService
from app.modules.traffic_visibility.repository import TrafficVisibilityRepository
from app.modules.traffic_visibility.service import TrafficVisibilityService


@pytest.fixture()
def connection_factory(tmp_path: Path):
    database_manager = DatabaseManager(tmp_path / "test.db")
    database_manager.initialize()
    return database_manager.connect


@pytest.fixture()
def device_service(connection_factory):
    repository = DeviceRepository(connection_factory)
    return DeviceService(repository)


@pytest.fixture()
def alert_service(connection_factory):
    return AlertService(AlertRepository(connection_factory), EventBus(), NotificationService())


@pytest.fixture()
def reporting_service(connection_factory):
    return ReportingService(connection_factory, ReportingEngine())


@pytest.fixture()
def monitoring_service(connection_factory):
    device_repository = DeviceRepository(connection_factory)
    dashboard_service = DashboardService(connection_factory, AlertService(AlertRepository(connection_factory), EventBus(), NotificationService()))
    return MonitoringService(
        connection_factory=connection_factory,
        device_repository=device_repository,
        dashboard_service=dashboard_service,
        alert_service=AlertService(AlertRepository(connection_factory), EventBus(), NotificationService()),
        event_bus=EventBus(),
        notifications=NotificationService(),
        heartbeat_engine=HeartbeatEngine(),
        port_engine=PortCheckEngine(),
        http_engine=HttpCheckEngine(),
        alert_engine=AlertEngine(),
        discovery_engine=NetworkDiscoveryEngine(HeartbeatEngine(), PortCheckEngine(), DiscoveryClassificationEngine()),
        settings_service=SettingsService(connection_factory),
    )


@pytest.fixture()
def traffic_visibility_service(connection_factory):
    device_repository = DeviceRepository(connection_factory)
    return TrafficVisibilityService(
        device_repository=device_repository,
        repository=TrafficVisibilityRepository(connection_factory),
        engine=TrafficVisibilityEngine(),
    )
