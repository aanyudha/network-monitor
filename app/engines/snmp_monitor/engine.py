from __future__ import annotations


class SnmpMonitorEngine:
    def is_available(self) -> bool:
        return False

    def status_message(self) -> str:
        return "SNMP monitoring is prepared as an extension point and not enabled in this release."

