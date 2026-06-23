from __future__ import annotations

from collections.abc import Callable


class NotificationService:
    def __init__(self) -> None:
        self._listeners: list[Callable[[str, str], None]] = []

    def subscribe(self, listener: Callable[[str, str], None]) -> None:
        self._listeners.append(listener)

    def notify(self, title: str, message: str) -> None:
        for listener in list(self._listeners):
            listener(title, message)

