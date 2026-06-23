from __future__ import annotations

import asyncio
import ipaddress
import socket

from app.core.models import DiscoveryResult
from app.engines.heartbeat.engine import HeartbeatEngine


class NetworkDiscoveryEngine:
    def __init__(self, heartbeat_engine: HeartbeatEngine) -> None:
        self._heartbeat_engine = heartbeat_engine

    async def discover(self, subnet: str, timeout_ms: int = 600) -> list[DiscoveryResult]:
        network = ipaddress.ip_network(subnet, strict=False)
        semaphore = asyncio.Semaphore(64)
        results: list[DiscoveryResult] = []

        async def probe(host: str) -> None:
            async with semaphore:
                heartbeat = await self._heartbeat_engine.check(host, timeout_ms)
                if heartbeat.reachable:
                    hostname = await asyncio.to_thread(self._resolve_hostname, host)
                    results.append(DiscoveryResult(ip_address=host, hostname=hostname, reachable=True))

        await asyncio.gather(*(probe(str(host)) for host in network.hosts()))
        results.sort(key=lambda item: item.ip_address)
        return results

    @staticmethod
    def _resolve_hostname(ip_address: str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except Exception:
            return ""

