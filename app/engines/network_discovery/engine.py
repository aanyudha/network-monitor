from __future__ import annotations

import asyncio
import ipaddress
import platform
import re
import socket
import ssl
import subprocess
from urllib import error, request

from app.core.models import DiscoveryFingerprint, DiscoveryResult
from app.engines.network_discovery.classification import DiscoveryClassificationEngine
from app.engines.heartbeat.engine import HeartbeatEngine
from app.engines.port_check.engine import PortCheckEngine


DISCOVERY_PORTS = [22, 23, 80, 139, 161, 443, 445, 515, 554, 631, 3306, 3389, 5432, 8000, 8080, 8443, 8899, 9100]
HTTP_PORTS = [80, 443, 8080, 8443]
TITLE_REGEX = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
MAC_REGEX = re.compile(r"((?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2})")


class NetworkDiscoveryEngine:
    def __init__(
        self,
        heartbeat_engine: HeartbeatEngine,
        port_engine: PortCheckEngine,
        classification_engine: DiscoveryClassificationEngine,
    ) -> None:
        self._heartbeat_engine = heartbeat_engine
        self._port_engine = port_engine
        self._classification_engine = classification_engine

    async def discover(self, subnet: str, timeout_ms: int = 600) -> list[DiscoveryResult]:
        network = ipaddress.ip_network(subnet, strict=False)
        semaphore = asyncio.Semaphore(64)
        results: list[DiscoveryResult] = []
        default_gateways = await asyncio.to_thread(self._detect_default_gateways)

        async def probe(host: str) -> None:
            async with semaphore:
                heartbeat = await self._heartbeat_engine.check(host, timeout_ms)
                if heartbeat.reachable:
                    hostname = await asyncio.to_thread(self._resolve_hostname, host)
                    open_ports = await self._probe_open_ports(host)
                    http_title, http_status_code, http_server = await self._probe_http_fingerprint(host, open_ports)
                    vendor_name = await asyncio.to_thread(self._resolve_vendor_name, host)
                    classification = self._classification_engine.classify(
                        DiscoveryFingerprint(
                            ip_address=host,
                            hostname=hostname,
                            open_ports=open_ports,
                            http_title=http_title,
                            http_status_code=http_status_code,
                            http_server=http_server,
                            vendor_name=vendor_name,
                            is_gateway=host in default_gateways,
                        )
                    )
                    results.append(
                        DiscoveryResult(
                            ip_address=host,
                            hostname=hostname,
                            reachable=True,
                            device_type=classification.device_type,
                            device_type_confidence=classification.confidence,
                            discovery_notes=classification.notes,
                            open_ports=open_ports,
                            http_title=http_title,
                            http_status_code=http_status_code,
                            vendor_name=vendor_name,
                            status="Reachable",
                        )
                    )

        await asyncio.gather(*(probe(str(host)) for host in network.hosts()))
        results.sort(key=lambda item: item.ip_address)
        return results

    async def _probe_open_ports(self, ip_address: str) -> list[int]:
        checks = await asyncio.gather(*(self._port_engine.check(ip_address, port, timeout_seconds=0.35) for port in DISCOVERY_PORTS))
        return sorted(result.port for result in checks if result.is_open)

    async def _probe_http_fingerprint(self, ip_address: str, open_ports: list[int]) -> tuple[str, int | None, str]:
        ports_to_try = [port for port in HTTP_PORTS if port in open_ports]
        for port in ports_to_try:
            title, status_code, server = await asyncio.to_thread(self._fetch_http_metadata, ip_address, port)
            if title or status_code is not None or server:
                return title, status_code, server
        return "", None, ""

    @staticmethod
    def _resolve_hostname(ip_address: str) -> str:
        try:
            hostname, _, _ = socket.gethostbyaddr(ip_address)
            return hostname
        except Exception:
            return ""

    @staticmethod
    def _fetch_http_metadata(ip_address: str, port: int) -> tuple[str, int | None, str]:
        scheme = "https" if port in {443, 8443} else "http"
        default_port = 443 if scheme == "https" else 80
        suffix = "" if port == default_port else f":{port}"
        url = f"{scheme}://{ip_address}{suffix}/"
        req = request.Request(url, headers={"User-Agent": "HeisenbergDiscovery/1.0"})
        try:
            context = ssl._create_unverified_context() if scheme == "https" else None
            with request.urlopen(req, timeout=1.2, context=context) as response:
                body = response.read(4096).decode(errors="ignore")
                title_match = TITLE_REGEX.search(body)
                title = " ".join(title_match.group(1).split())[:120] if title_match else ""
                server = response.headers.get("Server", "")
                return title, response.status, server
        except error.HTTPError as exc:
            return "", exc.code, exc.headers.get("Server", "")
        except Exception:
            return "", None, ""

    @staticmethod
    def _detect_default_gateways() -> set[str]:
        commands = [["route", "print", "0.0.0.0"]] if platform.system().lower().startswith("win") else [["ip", "route", "show", "default"], ["route", "-n"]]
        for command in commands:
            try:
                completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=2)
            except Exception:
                continue
            output = completed.stdout or ""
            gateways = {
                ip
                for ip in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", output)
                if ip != "0.0.0.0"
            }
            if gateways:
                return gateways
        return set()

    @staticmethod
    def _resolve_vendor_name(ip_address: str) -> str:
        commands = [["arp", "-a", ip_address]] if platform.system().lower().startswith("win") else [["arp", "-n", ip_address]]
        for command in commands:
            try:
                completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=2)
            except Exception:
                continue
            match = MAC_REGEX.search(completed.stdout or "")
            if match:
                return f"MAC {match.group(1).replace('-', ':').upper()}"
        return ""
