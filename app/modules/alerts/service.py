from __future__ import annotations

from app.core.event_bus.bus import EventBus
from app.core.notifications.service import NotificationService
from app.modules.alerts.repository import AlertRepository


class AlertService:
    def __init__(self, repository: AlertRepository, event_bus: EventBus, notifications: NotificationService) -> None:
        self._repository = repository
        self._event_bus = event_bus
        self._notifications = notifications

    def create_alert(self, alert) -> None:
        saved = self._repository.create(alert)
        self._event_bus.publish("alert.created", saved)
        self._notifications.notify("Network alert", saved.message)

    def resolve(self, device_id: int, alert_type: str) -> None:
        self._repository.resolve_open(device_id, alert_type)

    def recent_alerts(self, limit: int = 10):
        return self._repository.list_recent(limit)

    def all_alerts(self):
        return self._repository.list_all()

