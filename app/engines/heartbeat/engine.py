from __future__ import annotations

import asyncio
import platform
import re

from app.core.models import HeartbeatResult


LATENCY_REGEX = re.compile(r"time[=<]?\s*(\d+(?:\.\d+)?)\s*ms", re.IGNORECASE)
LOSS_REGEX = re.compile(r"(\d+(?:\.\d+)?)%\s*(?:packet loss|loss)", re.IGNORECASE)


class HeartbeatEngine:
    async def check(self, ip_address: str, timeout_ms: int) -> HeartbeatResult:
        args = self._build_command(ip_address, timeout_ms)
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
        except FileNotFoundError:
            return HeartbeatResult(False, None, None, error="ping command not available")
        except Exception as exc:  # pragma: no cover - defensive runtime path
            return HeartbeatResult(False, None, None, error=str(exc))

        output = (stdout or b"").decode(errors="ignore") + "\n" + (stderr or b"").decode(errors="ignore")
        latency = self.parse_latency(output)
        packet_loss = self.parse_packet_loss(output)
        reachable = process.returncode == 0
        error = "" if reachable else output.strip().splitlines()[-1] if output.strip() else "Ping failed"
        return HeartbeatResult(reachable=reachable, latency_ms=latency, packet_loss=packet_loss, error=error)

    def _build_command(self, ip_address: str, timeout_ms: int) -> list[str]:
        if platform.system().lower().startswith("win"):
            return ["ping", "-n", "1", "-w", str(timeout_ms), ip_address]
        timeout_seconds = max(1, round(timeout_ms / 1000))
        return ["ping", "-c", "1", "-W", str(timeout_seconds), ip_address]

    @staticmethod
    def parse_latency(output: str) -> float | None:
        match = LATENCY_REGEX.search(output)
        return float(match.group(1)) if match else None

    @staticmethod
    def parse_packet_loss(output: str) -> float | None:
        match = LOSS_REGEX.search(output)
        return float(match.group(1)) if match else None

